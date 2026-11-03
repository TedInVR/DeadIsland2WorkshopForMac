"""Independent DI2 chunk framing; Zstandard and CityHash libraries handle compression/hash.
Format reference: SteffenL/file-format-docs, games/dead-island-2 (no template code bundled).
"""
import struct
LIMIT=128*1024*1024
END=b'\x42\xfc\x13\x5a'
MAGIC=b'\x28\xb5\x2f\xfd'
class CodecError(ValueError):pass

def libraries():
    try:import zstandard,cityhash
    except ImportError:raise CodecError('Compression support is missing. Reinstall the current Workshop update to repair its private runtime.') from None
    return zstandard,cityhash

def decode(raw):
    if len(raw)<33 or raw[29:33]!=MAGIC:return raw,None
    zstd,city=libraries();parts=[];chunks=[];p=21;total=0
    try:
        while raw[p:p+4]!=END:
            if p+8>len(raw):raise CodecError('Truncated compressed-save chunk header.')
            compressed,size=struct.unpack_from('<II',raw,p);start=p;p+=8
            if not 0<compressed<=LIMIT or not 0<size<=65536 or p+compressed>len(raw):raise CodecError('Invalid compressed-save chunk length.')
            total+=size
            if total>LIMIT:raise CodecError('Expanded save exceeds 128 MB.')
            frame=raw[p:p+compressed]
            if zstd.frame_content_size(frame)!=size:raise CodecError('Compressed-save frame size mismatch.')
            value=zstd.ZstdDecompressor(max_window_size=128*1024).decompress(frame,max_output_size=size,allow_extra_data=False)
            if len(value)!=size:raise CodecError('Compressed-save chunk length mismatch.')
            p+=compressed;parts.append(value);chunks.append((value,raw[start:p]))
        if not parts or p+12!=len(raw):raise CodecError('Invalid compressed-save footer.')
        body=b''.join(parts)
        if city.CityHash64(body)!=struct.unpack_from('<Q',raw,p+4)[0]:raise CodecError('Compressed-save checksum does not match. Use an intact backup.')
        return raw[:21]+body,{'original':raw,'plain':raw[:21]+body,'chunks':chunks}
    except (struct.error,zstd.ZstdError) as e:raise CodecError('The compressed save is damaged or unsupported.') from e

def encode(plain,state):
    if state is None:return plain
    if plain==state['plain']:return state['original']
    if len(plain)>LIMIT or plain[:21]!=state['plain'][:21]:raise CodecError('Invalid edited save header or size.')
    zstd,city=libraries();body=plain[21:];parts=[plain[:21]];compressor=zstd.ZstdCompressor(level=3)
    for index,p in enumerate(range(0,len(body),65536)):
        value=body[p:p+65536]
        if index<len(state['chunks']) and state['chunks'][index][0]==value:parts.append(state['chunks'][index][1])
        else:
            frame=compressor.compress(value);parts.append(struct.pack('<II',len(frame),len(value))+frame)
    parts.append(END+struct.pack('<Q',city.CityHash64(body)))
    raw=b''.join(parts)
    if decode(raw)[0]!=plain:raise CodecError('Recompressed save failed verification.')
    return raw
