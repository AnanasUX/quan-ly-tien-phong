import re

with open('src/App.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('30.4°', '{data.weather.temp}°')
code = code.replace('30.4', '{data.weather.temp}')
code = code.replace('Mây thưa ☁️', '{data.weather.condition}')
code = code.replace('Cảm nhận như 36.4°C', 'Cảm nhận như {data.weather.feels_like}°C')
code = code.replace('36.4°C', '{data.weather.feels_like}°C')
code = code.replace('71%', '{data.weather.humidity}%')
code = code.replace('39.38', '{data.weather.pm25}')
code = code.replace('12 km/h', '{data.weather.wind} km/h')
code = code.replace('14 km/h', '{data.weather.wind} km/h')
code = code.replace('Quận Hà Đông, Hà Nội', '{data.weather.location}')
code = code.replace('📍 Hà Đông, Hà Nội', '📍 {data.weather.location}')
code = code.replace('Hà Đông, Hà Nội', '{data.weather.location}')

header = """import { createContext, useContext, useState, useEffect } from "react";
import LZString from "lz-string";

const defaultData = {
  weather: {
     temp: "30.4",
     condition: "Mây thưa ☁️",
     feels_like: "36.4",
     humidity: "71",
     pm25: "39.38",
     wind: "12",
     location: "Quận Hà Đông, Hà Nội",
  }
};
const DataContext = createContext(defaultData);
const useData = () => useContext(DataContext);
"""

code = header + '\n' + code

code = code.replace('function MobileLayout() {', 'function MobileLayout() {\n  const data = useData();')
code = code.replace('function TabletLayout() {', 'function TabletLayout() {\n  const data = useData();')
code = code.replace('function DesktopLayout() {', 'function DesktopLayout() {\n  const data = useData();')

root_new = """export default function App() {
  const [data, setData] = useState(defaultData);
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const d = params.get("data");
    if (d) {
      try {
        const decoded = LZString.decompressFromEncodedURIComponent(d);
        if (decoded) {
            setData(JSON.parse(decoded));
        }
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  return (
    <DataContext.Provider value={data}>
      <div className="min-h-screen w-full bg-[#f4f6fa]">
        <div className="md:hidden"><MobileLayout /></div>
        <div className="hidden md:block xl:hidden"><TabletLayout /></div>
        <div className="hidden xl:block"><DesktopLayout /></div>
      </div>
    </DataContext.Provider>
  );
}"""

code = re.sub(r'export default function App\(\) \{.*\}', root_new, code, flags=re.DOTALL)

with open('src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
