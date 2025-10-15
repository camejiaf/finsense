# FinSense 

This is my financial analysis app that I built because I got tired of spreadsheets and wanted something chill.

## What's Cool About It

### The Good Stuff
- **DCF Analysis** - Discounted cash flow modeling that actually makes sense
- **Real Stock Data** - Pulls live prices from Alpha Vantage 
- **Demo Mode** - When the API runs out of calls, it switches to realistic fake data
- **Export Reports** - Spit out Excel/PDF reports that look professional
- **History Tracking** - Remembers your last few analyses so you can compare

### The Technical Magic
- **Monte Carlo** - Runs 1000+ scenarios to see what could happen
- **Recession Mode** - Built-in "what if the economy goes to hell" scenarios
- **Smart Diagnostics** - Tells you when your model is probably wrong
- **Rate Limiting** - Doesn't blow through API calls like a maniac
- **Clean UI** - Actually looks modern, not like it's from 2005

## How It's Built

### Frontend Stuff
- **Next.js 15** - React but faster and cooler
- **TypeScript** - Because JavaScript without types is chaos
- **Tailwind CSS** - Makes styling actually enjoyable
- **localStorage** - Remembers stuff between sessions

### Backend Stuff
- **FastAPI** - Python API that's actually fast
- **Alpha Vantage** - Gets real stock data (when it feels like it)
- **Custom DCF Engine** - Built with numpy because I'm not a masochist
- **Export Magic** - Turns your analysis into classic Excel/PDF files

### The Files That Matter
```
utils/
├── dcf_calc.py          # The brain - does all the math
├── data_fetch.py        # Talks to Alpha Vantage, has demo mode
├── demo_data.py         # Makes fake data that looks real
├── excel_exporter.py    # Spits out Excel files
└── pdf_generator.py     # Makes PDFs that don't look terrible
```

## Getting Started

### What You Need
- Python 3.8+ 
- Node.js 18+ 
- Alpha Vantage API key

### Quick Setup
```bash
# Backend stuff
cd backend
pip install -r requirements.txt

# Frontend stuff  
cd frontend
npm install
```

### Configuration
1. Copy `.env.example` to `.env` in the backend folder:
```bash
cp backend/.env.example backend/.env
```

2. Edit `backend/.env` and add your actual Alpha Vantage API key:
```env
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
MIN_REQUEST_INTERVAL=12
```

**🔒 Security Note**: Never commit your `.env` 

### Running It
```bash
# Easy way - starts everything
./start_dev.bat

# Or if you're a masochist, run them separately:
# Backend: cd backend && python run_backend.py
# Frontend: cd frontend && npm run dev
```

## The Math

### Monte Carlo Magic
- **Fat Tails** - Uses Student's t-distribution because markets are wild
- **Recession Mode** - 15% chance the economy goes sideways
- **Vectorized Math** - Numpy makes it fast (1000+ scenarios in seconds)
- **Sensitivity Testing** - Shakes up all the assumptions to see what breaks

### Smart Diagnostics
- **Terminal Value Check** - Yells at you if 90% of your value comes from the far future
- **Duration Math** - Shows when you're getting your money back
- **Health Warnings** - Points out when your model is probably garbage
- **Scenario Samples** - Shows you exactly what inputs gave crazy results

### Demo Data (When APIs Suck)
- **Hourly Changes** - Fake data rotates every hour so it's not boring
- **Realistic Prices** - Uses actual market caps, just tweaked
- **Full Financials** - Income statements, balance sheets, the whole shebang
- **Price History** - 30 days of fake but believable price movements

## How to Use It

### Basic Analysis
1. Pick a stock from the dropdown (AAPL, MSFT, GOOGL)
2. Mess with the WACC and terminal growth numbers
3. Hit "Run Analysis" and watch the magic happen
4. Export to Excel/PDF if you want to show off

### Demo Mode
- Kicks in automatically when the API runs out of calls
- Uses realistic fake data that rotates every hour
- Shows a "DEMO MODE" banner 

### History Feature
- Saves your last analyses automatically
- Compare different scenarios side by side
- Export any previous analysis

## Technical Stuff

### API Management
- Alpha Vantage gives you 25 calls/day for free
- Caches data for 5 minutes so it doesn't spam the API
- Automatically switches to demo data when you hit the limit
- You can manually toggle demo mode for presentations

### Error Handling
- Catches API errors and doesn't crash
- Falls back to demo data gracefully
- Shows actual error messages 
- Retries failed requests with smart delays

### Performance
- Uses numpy vectorization (it's fast)
- Caches everything it can
- Only makes API calls when necessary
- UI doesn't freeze during calculations

## Example Output

### What You'll See
- **Current Price**: $247.66
- **DCF Value**: $285.42
- **Upside**: +15.2%
- **Recommendation**: BUY

### Monte Carlo Results
- **Average**: $285.42
- **Range (5th-95th)**: $245.18 - $328.76
- **Standard Deviation**: $41.23

### Model Health Check
- **Terminal Value Share**: 67%
- **Duration**: 4.2 years


### Production Stuff
- Environment variables for config
- Proper authentication (recommended for production)
- HTTPS enforcement
- Database security (if you add user data)
- CORS setup for cross-origin requests
- Proper error logging
- Smart API rate limiting
- Clean export formatting

### Why This is Cool
- Clean, readable codebase
- Actually useful documentation
- Advanced financial modeling
- Real API integration
- Production-ready architecture

## License

This is just for showing off my skills. Feel free to look at the code, learn from it, or use it as inspiration for your own projects.

