# 🏷️ Simple Price Watcher

This project provides a simple yet effective way for users to track the prices of specific online items. It leverages Docker containers, allowing for easy parallelization to monitor multiple items simultaneously, with each item tracked by a dedicated container instance.

A unique aspect of this project is its **AI-driven development** 🤖. It is primarily being developed by **Gemini Code Assist**, an AI coding assistant. My role, as the user, is that of a "techie product owner" 🧑‍💻 – guiding the development, providing specifications, assisting in complex problem-solving, and rigorously testing the project. This collaborative approach 🤝 showcases the evolving landscape of software development with AI.

## 🚀 How It Works

The core process for each tracked item is as follows:
1.  📥 **Fetch**: The script retrieves the content of the specified product URL.
2.  🔎 **Scrape**: It then parses the HTML to extract the product's current price and name using predefined CSS selectors.
3.  ⚖️ **Compare**: The current price is compared against previously recorded prices.
4.  🔔 **Notify**: If a price drop (or a significant change, depending on future enhancements) is detected, a notification is sent via Telegram, including a price history graph.
5.  🔄 **Repeat**: The process repeats after a configurable delay.

## 🕸️ Web Scraping

To ensure standardization and ease of extension to different websites, the project employs web scraping techniques using **Beautiful Soup**. For each product, it extracts two key pieces of information:

-   **Product Price**: Identified using the `PRODUCT_PRICE_SELECTOR`.
-   **Product Name**: Identified using the `PRODUCT_NAME_SELECTOR`.

These selectors are provided as environment variables. You will need to inspect the HTML structure of the product webpage to determine the correct CSS selectors for the items you wish to track.

## 🐳 Docker

The application is designed to run within Docker containers, providing isolation and simplifying deployment.

### Dockerfile
The `Dockerfile` uses a Python base image and executes the main tracking script. For scheduling periodic checks, the Python script implements a `while True` loop with a configurable delay. An earlier attempt to use a cron-based scheduler within the container did not yield the expected results, leading to the current loop-based approach.

### Docker Compose
The `docker-compose.yml` file simplifies the management of the Docker container. It is configured to:
-   Build the Docker image from the provided `Dockerfile`.
-   Run the container with the necessary environment variables.

The example values in the `docker-compose.yml` are illustrative and should be replaced with your specific product details and credentials.

## ⚙️ Configuration (Environment Variables)

The Docker image requires several environment variables to be set for proper operation:

-   `URL`: The full URL of the product page to track.
    *   Example: `https://store-eu.gl-inet.com/es/products/eu-beryl-ax-gl-mt3000-pocket-sized-ax3000-wi-fi-6-travel-router-with-2-5g-wan-port`
-   `PRODUCT_PRICE_SELECTOR`: The CSS selector to locate the product's price element on the webpage.
    *   Example: `span.money[data-price]`
-   `PRODUCT_NAME_SELECTOR`: The CSS selector to locate the product's name element on the webpage.
    *   Example: `h2.product-title`
-   `TELEGRAM_TOKEN`: Your Telegram Bot API token. This is required for sending notifications.
    *   Example: `123456:ABC-DEF1234ghIkl-zyx57W2v1u0T`
-   `TELEGRAM_CHAT_ID`: The chat ID (user or group) where the Telegram bot should send notifications.
    *   Example: `123456789`
-   `DELAY_SECONDS`: The interval (in seconds) between consecutive price checks.
    *   Example: `3600` (for 1 hour)
-   `DB_TYPE`: The type of database to use. Defaults to `sqlite`.
    *   Example: `sqlite` or `postgres` (if support is added)
-   `DB_HOST`: The hostname or IP address of the database server (used if `DB_TYPE` is not `sqlite`).
    *   Example: `localhost` or `your-db-host.com`
-   `DB_PORT`: The port number of the database server (used if `DB_TYPE` is not `sqlite`).
    *   Example: `5432` (for PostgreSQL)
-   `DB_USER`: The username for connecting to the database (used if `DB_TYPE` is not `sqlite`).
    *   Example: `price_user`
-   `DB_PASSWORD`: The password for connecting to the database (used if `DB_TYPE` is not `sqlite`).
    *   Example: `supersecretpassword`
-   `DB_NAME`: The name of the database (used if `DB_TYPE` is not `sqlite`).
    *   Example: `price_tracker_db`
-   `API_HOST`: The host address for the API to listen on. Defaults to `0.0.0.0`.
    *   Example: `0.0.0.0` (to listen on all available network interfaces) or `127.0.0.1` (for localhost only)
-   `API_PORT`: The port for the API to listen on. Defaults to `8000`.
    *   Example: `8000`

## ✈️ Telegram

Notifications for price changes are sent using a Telegram bot. When a price drop is detected, the bot sends a message containing:
-   The product name.
-   The old price.
-   The new (current) price.
-   A direct link to the product page.
-   A graphical image visualizing the price history, allowing for a quick overview of price trends.

![Price history graphic example](docs/assets/price_history.png)
---

*This README is also co-authored by Gemini Code Assist 🤖, reflecting the collaborative nature of the project.*
