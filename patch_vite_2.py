with open('vite.config.ts', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("base: '/quan-ly-tien-phong-web/'", "base: '/quan-ly-tien-phong/'")
with open('vite.config.ts', 'w', encoding='utf-8') as f:
    f.write(text)
