# Agent – Web Crawling and AI-Augmented Agent

This project represents an intelligent agent system capable of crawling the web, scraping specific content (including dynamic pages like eMAG), applying semantic filters, and optionally interacting with AI-based tools for data processing or enrichment. The architecture is modular, separating crawling, scraping, decision logic, and tool execution.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue) ![Version](https://img.shields.io/badge/version-1.0.0-orange)

---

## 🧠 Project Overview

- **Language**: Python 3
- **Core Libraries**: `asyncio`, `aiohttp`, `json`, `re`, `uuid`, `os`, `redis`, `playwright`
- **Main Components**:
  - `agent/`: Logic for decision-making and intelligent behavior
  - `crawler/`: Responsible for both static and dynamic web scraping + Wikipedia crawling
  - `main.py`: Entry point that integrates agent + crawler + tool functions

## 🗂️ Project Structure

```
Agent/
├── agent/
│   ├── __init__.py
│   ├── agent.py           # The intelligent agent core
│   ├── tool_funcs.py      # Tool functions the agent can invoke
│   └── tools.py           # Mapping of tools
├── crawler/
│   ├── __init__.py
│   ├── crawl.py           # Wikipedia crawler with depth control + Redis URL caching
│   ├── scrap.py           # Web scraping for weather and structured data
│   └── dynamic_scraper.py # Playwright-powered dynamic content scraper (eMAG support)
├── data/
│   ├── filter.json        # Subject keywords for relevance filtering
│   ├── linksJson.json     # Crawled Wikipedia links
│   ├── product.json       # Result storage from scraping
│   └── test.json          # Output for debug/test
└── main.py                # Main integration script
```

## 🔍 Function Descriptions

### `main.py`
- Loads and initializes the agent.
- Sends an initial prompt to the agent (`"weather in London"` by default).
- The agent parses the prompt, checks if a tool is needed, and calls it.

### `agent/agent.py`
- Core LLM-based agent logic.
- Chooses tools using a mapping (`tools` dict).
- Executes tool functions and formats the results as agent responses.

### `agent/tool_funcs.py`
Callable tools include:
- `crawlSubjectFunc(subject: str, depth: int)` – Wikipedia crawler with Redis caching.
- `scrapWeatherFunc(location: str)` – Web scraper for weather.
- `calculateFunc(expression: str)` – Mathematical evaluator.
- `scrapeDynamicProduct(link: str)` – Uses Playwright to extract product name, price, and specs from eMAG.

### `crawler/crawl.py`
- Wikipedia crawler with `asyncio` and `aiohttp`.
- Controls crawling depth and applies filters from `filter.json`.
- Uses Redis to **cache visited URLs**, preventing redundant work and improving performance.

### `crawler/scrap.py`
- Static scraping using aiohttp and regex/html parsing.
- Designed for structured info like weather.

### `crawler/dynamic_scraper.py`
- Dynamic headless browser-based scraping using `Playwright`.
- Extracts live data (name, price, description) from pages like eMAG.
- Supports product scraping for dynamic content, including `div`-rendered prices or JS-loaded specs.

## 📁 Data Files

- `filter.json`: Semantic filtering keywords.
- `linksJson.json`: Crawled URLs.
- `product.json`: Scraped data from product pages (eMAG etc).
- `test.json`: Output testing.

## 🚀 How to Run

```bash
# Clone the repository
git clone https://github.com/AMihneaa/Agent.git
cd Agent

# Install dependencies
pip install aiohttp redis playwright

# For Playwright (first-time setup)
playwright install

# Run the agent
python main.py
```

Sample prompts in `main.py`:
```python
run_agent("calculate 2 + 2")
run_agent("scrap weather in Bucharest")
run_agent("crawl subject Artificial Intelligence depth 2")
run_agent("scrape emag link https://www.emag.ro/product-id")
```

## 🧠 How It Works

- The agent parses user prompts and checks for tool calls.
- If tool needed, it dynamically invokes Python functions (e.g., scrape weather, crawl Wikipedia).
- The crawler uses Redis to store and check previously visited links → reduces redundancy.
- Playwright is used for dynamic page scraping, useful for modern e-commerce websites.

## 🔮 Future Improvements

- Add tool selection via a local LLM (e.g., DeepSeek or OpenAI via API).
- Automatic product classification based on content.
- Integration with vector databases for semantic memory.
- Embed product summaries using LLM.

## 🤝 Contributing

We welcome contributions to this project! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Built by Mihnea – for intelligent automation and web interaction with Python.

## ❓ FAQ

**Q: How do I install dependencies?**
A: Use the command `pip install -r requirements.txt`.

**Q: Can I contribute to this project?**
A: Yes, contributions are welcome! Please refer to the Contributing section.
