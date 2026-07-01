from pdf2image import convert_from_path
from io import BytesIO

pages = convert_from_path(
    r'I:\Visual_Studio_Code\CyberOps_Fall2026\processed\AJ_lab02_pending.pdf',
    dpi=100,
    poppler_path=r'C:\poppler\poppler-26.02.0\Library\bin',
    fmt='jpeg'
)
total = 0
for p in pages:
    buf = BytesIO()
    p.save(buf, format='JPEG', quality=70)
    total += len(buf.getvalue())
print(f'Pages: {len(pages)}')
print(f'Total size per student: {total/1024/1024:.1f} MB')
print(f'Estimated 29 students: {total*29/1024/1024:.0f} MB')
print(f'Estimated 15 students: {total*15/1024/1024:.0f} MB')

