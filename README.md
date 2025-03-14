# Simple Price Watcher 
This project aims to help users to tracker specific items price. It is develop under a container so it is easy to parallelize multiple items with different containers. The tracker is a simple project to point to one article per docker.

## Scrap
In order to be more standar and easy to extend to different web, the project is scrapping the url and getting two items with Soup
- price_element: soup.select(price_selector)
- product_name_element: soup.select(name_selector)
Being the price_selector and name_salector variables the environment variables in the docker compose, so it is needed to inspect the product webpage to get the info. 

## Docker
The docker file is using a Python image and running the script. A cron scheduler approach was tried but not get to work as expected. In order to schedule the runs, the python script is in a while true loop delaying the next trigger

### Docker Compose
The docker compose is configure to build the provided dockerfile in a new image.
The values for the product are example of a personal run

## Telegram
A telegram bot is used to notified the sales! The message includes relevant info and a graphic image to check the history.
![Price history graphic example](assets/price_history.png)
