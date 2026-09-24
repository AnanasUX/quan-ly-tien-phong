import re

with open('vite.config.ts', 'r', encoding='utf-8') as f:
    text = f.read()
    
text = text.replace('export default defineConfig({', "export default defineConfig({\n  base: '/quan-ly-tien-phong-web/',")

with open('vite.config.ts', 'w', encoding='utf-8') as f:
    f.write(text)
