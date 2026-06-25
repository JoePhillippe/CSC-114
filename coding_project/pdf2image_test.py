from pdf2image import convert_from_path
pages = convert_from_path(
    'I:/Visual_Studio_Code/CyberOps_Fall2026/queue/KH_lab04_pending.pdf',
    poppler_path=r'C:\poppler\poppler-26.02.0\Library\bin'
)
print(f'Pages converted: {len(pages)}')
print('pdf2image with poppler ready')
