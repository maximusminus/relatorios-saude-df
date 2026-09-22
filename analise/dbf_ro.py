"""Leitor de .dbc do DATASUS que NÃO escreve no saudedf: descomprime num diretório temporário."""
import os, struct, tempfile, datasus_dbc, dbfread

def ler(dbc):
    fd, dbf = tempfile.mkstemp(suffix='.dbf'); os.close(fd)
    try:
        datasus_dbc.decompress(dbc, dbf)
        with open(dbf, 'r+b') as f:            # terminador 0x00 → 0x0D (mesmo reparo do saudedf)
            hl = struct.unpack('<H', f.read(32)[8:10])[0]
            f.seek(hl - 1)
            if f.read(1) == b'\x00':
                f.seek(hl - 1); f.write(b'\x0d')
        yield from dbfread.DBF(dbf, encoding='latin-1', load=False, char_decode_errors='replace')
    finally:
        os.remove(dbf)
