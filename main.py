from scripts.scraper import search_youtube
import pandas as pd


def main():
    video_list_size = 250
    amount_weeks = 4
    topic = "langchain"
    search_youtube_res = search_youtube(topic, video_list_size, amount_weeks)

    # TODO: Use LLM to process the results
    df = pd.DataFrame(search_youtube_res)
    print(df)


if __name__ == "__main__":
    main()
