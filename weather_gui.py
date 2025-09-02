# weather_gui.py
import os
import io
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise SystemExit("Set OPENWEATHER_API_KEY in environment or .env")

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"  # 5 day / 3 hour

ICON_URL = "http://openweathermap.org/img/wn/{}@2x.png"

def fetch_weather(q=None, lat=None, lon=None, units="metric"):
    params = {"appid": API_KEY, "units": units}
    if q:
        params["q"] = q
    else:
        params["lat"] = lat
        params["lon"] = lon
    r = requests.get(WEATHER_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_forecast(q=None, lat=None, lon=None, units="metric"):
    params = {"appid": API_KEY, "units": units}
    if q:
        params["q"] = q
    else:
        params["lat"] = lat
        params["lon"] = lon
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# Simple IP-based geolocation (works on desktop)
def my_location():
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return float(data["lat"]), float(data["lon"])
    except Exception:
        return None, None

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.geometry("420x520")
        self.resizable(False, False)
        self.icon_img = None  # to keep reference
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Input row
        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(frm, textvariable=self.city_var, width=28)
        city_entry.grid(row=0, column=0, padx=(0,6))
        city_entry.insert(0, "Bengaluru")

        get_btn = ttk.Button(frm, text="Get Weather", command=self.on_get_weather)
        get_btn.grid(row=0, column=1)

        loc_btn = ttk.Button(frm, text="Use My Location", command=self.on_use_location)
        loc_btn.grid(row=1, column=0, columnspan=2, pady=(6,12), sticky="ew")

        # Unit toggle
        self.unit = tk.StringVar(value="metric")
        units_frame = ttk.Frame(frm)
        units_frame.grid(row=2, column=0, columnspan=2, pady=(0,8))
        ttk.Radiobutton(units_frame, text="°C", variable=self.unit, value="metric").pack(side="left")
        ttk.Radiobutton(units_frame, text="°F", variable=self.unit, value="imperial").pack(side="left")

        # Weather display frame
        self.city_label = ttk.Label(frm, text="", font=("Helvetica", 14, "bold"))
        self.city_label.grid(row=3, column=0, columnspan=2, pady=(6,2))

        self.icon_label = ttk.Label(frm)
        self.icon_label.grid(row=4, column=0, columnspan=2)

        self.cond_label = ttk.Label(frm, text="", font=("Helvetica", 11))
        self.cond_label.grid(row=5, column=0, columnspan=2)

        self.temp_label = ttk.Label(frm, text="", font=("Helvetica", 18))
        self.temp_label.grid(row=6, column=0, columnspan=2, pady=(8,0))

        self.detail_label = ttk.Label(frm, text="", font=("Helvetica", 10))
        self.detail_label.grid(row=7, column=0, columnspan=2, pady=(6,0))

        # Forecast area (simple text)
        ttk.Separator(frm, orient="horizontal").grid(row=8, column=0, columnspan=2, sticky="ew", pady=10)
        self.forecast_frame = ttk.Frame(frm)
        self.forecast_frame.grid(row=9, column=0, columnspan=2, sticky="nsew")

        self.forecast_text = tk.Text(self.forecast_frame, height=8, width=48, wrap="word")
        self.forecast_text.pack(side="left", fill="both", expand=True)
        self.forecast_text.configure(state="disabled")

    def on_get_weather(self):
        q = self.city_var.get().strip()
        if not q:
            messagebox.showinfo("Input needed", "Enter a city name or click Use My Location.")
            return
        self.fetch_and_display(q=q)

    def on_use_location(self):
        lat, lon = my_location()
        if lat is None:
            messagebox.showerror("Location failed", "Could not detect location via IP.")
            return
        self.fetch_and_display(lat=lat, lon=lon)

    def fetch_and_display(self, q=None, lat=None, lon=None):
        units = self.unit.get()
        try:
            data = fetch_weather(q=q, lat=lat, lon=lon, units=units)
        except requests.HTTPError as e:
            try:
                msg = e.response.json().get("message", str(e))
            except Exception:
                msg = str(e)
            messagebox.showerror("API error", msg)
            return
        except requests.RequestException as e:
            messagebox.showerror("Network error", str(e))
            return

        # Fill top info
        name = data.get("name", "")
        country = data.get("sys", {}).get("country", "")
        weather_desc = data.get("weather", [{}])[0].get("description", "").title()
        temp = data.get("main", {}).get("temp")
        feels = data.get("main", {}).get("feels_like")
        humidity = data.get("main", {}).get("humidity")
        wind = data.get("wind", {}).get("speed")
        units_label = "°C" if units == "metric" else "°F"

        self.city_label.config(text=f"{name}, {country}")
        self.cond_label.config(text=weather_desc)
        self.temp_label.config(text=f"{temp} {units_label}")
        self.detail_label.config(text=f"Feels like: {feels} {units_label} | Humidity: {humidity}% | Wind: {wind} m/s")

        # Icon
        icon_code = data.get("weather", [{}])[0].get("icon")
        if icon_code:
            try:
                img_resp = requests.get(ICON_URL.format(icon_code), timeout=8)
                img_resp.raise_for_status()
                img_data = img_resp.content
                pil_img = Image.open(io.BytesIO(img_data)).resize((100,100))
                self.icon_img = ImageTk.PhotoImage(pil_img)
                self.icon_label.config(image=self.icon_img)
            except Exception:
                self.icon_label.config(image="")

        # Forecast (short)
        try:
            fc = fetch_forecast(q=q, lat=lat, lon=lon, units=units)
            # build simple readable forecast: show next 5 entries (3-hour steps)
            items = fc.get("list", [])[:5]
            text = ""
            for it in items:
                dt = it.get("dt_txt", "—")
                t = it.get("main", {}).get("temp", "—")
                desc = it.get("weather", [{}])[0].get("description", "").title()
                text += f"{dt} — {t}{units_label} — {desc}\n"
            self.forecast_text.configure(state="normal")
            self.forecast_text.delete("1.0", "end")
            self.forecast_text.insert("1.0", text)
            self.forecast_text.configure(state="disabled")
        except Exception:
            # ignore forecast errors but clear text
            self.forecast_text.configure(state="normal")
            self.forecast_text.delete("1.0", "end")
            self.forecast_text.insert("1.0", "No forecast available.")
            self.forecast_text.configure(state="disabled")

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
