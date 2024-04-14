
from translate import Translation
from sentiment import classifier
import tweepy
import re
from twitter import search_twitter as tweet
import os
from dotenv import load_dotenv
import pandas as pd

import requests
from app import app
import uvicorn

from dataplotting import plotpie, plotlc

import logging
logging.basicConfig(level=logging.INFO,filename="twitter_project.log",filemode='w',format="%(asctime)s - %(levelname)s - %(message)s")



def run():
    
    api_url = "http://127.0.0.1:8000/search_query/1"
    request =requests.get(api_url)
    
    try:
        request.status_code == 200
        string_value = request.json()
        logging.info(f"\n\n Search String = {string_value.get('name')}")
    except:
        logging.error("\n\n Unable to Get data from web server")

    
    try:
        client = tweet.initialise()
        logging.info(f"\n\n Twitter API Got Initialized")
        
    except "Tweet_initialize_error" as e:
        logging.error("\n\n Unable to Initialize Tweet")
    
   
      
    try:
        response = client.get_recent_tweets_count(query = string_value.get('name'),granularity='day')
        val = 1/len(response)
        logging.info(f"Recent tweets count for a week is received")

        tweets_cnt_container= [[tweetcnt['start'][:10],tweetcnt['tweet_count']] for tweetcnt in response.data]  
        columns=['date', 'tweets count']
        tweetstweets_count_df = pd.DataFrame(tweets_cnt_container,columns=columns)
        logging.info(f"tweets_count_df {tweetstweets_count_df}")

        tweetstweets_count_df.to_csv('tweetcount.csv', index=True)
        logging.info(f"\n\n tweets count written in tweetcount.csv")
        
        
            
    except ZeroDivisionError as e:
        logging.info("\n\n No Recent tweets")
        pass

    except "tweetcount.csv file is already open" as e:
        logging.error("\n\n Please close the tweetcount.csv file as it cannot write it and it will process only the old data")
        pass
    

    try:

        response = client.search_recent_tweets(query = string_value.get('name') ,max_results=10, tweet_fields=['public_metrics','created_at'],expansions=['author_id'])
        value = 1/len(response)
        tweets_container= [[tweetread.id,tweetread.text,tweetread.created_at,tweetread.public_metrics['like_count'],tweetread.public_metrics['retweet_count'],tweetread.public_metrics['impression_count']] for tweetread in response.data]  
        columns=['tweet_ids', 'tweets text','created_at','like_count','retweet_count','impression_count']
        
        logging.info(f"\n\n tweets{tweets_container}")
        tweets_df = pd.DataFrame(tweets_container,columns=columns)
        logging.info(f"\n\n result count {response.meta['result_count']}")
        val = str(response.includes)
        logging.info(f"\n\n response {val}")
        userid = re.findall("User id=(.*?) name=",val)
        name = re.findall("name=(.*?) userna",val)
        username = re.findall("username=(.*?)>",val)
        tweets_df['userid'] = userid
        tweets_df['name'] = name
        tweets_df['username'] = username
        followers =[]
        image =[]
  
        for i in range(response.meta['result_count']):
            response = client.get_user(id=userid[i],user_fields=['public_metrics','profile_image_url'])
            user_metrics = response.data['public_metrics']
            followers.append(user_metrics['followers_count'])
            image_details = response.data['profile_image_url']
            image.append(image_details)
    
    except ZeroDivisionError as e:
        logging.info("\n\nNo search Recent tweets")
        pass

    
       

    tweets_df['followers']=followers
    tweets_df['image']=image
    tweets_df['toenglish']=[Translation(twee) for twee in tweets_df['tweets text']]
    tweets_df['sentiment']=[classi['label'] for classi in classifier(list(tweets_df['toenglish']))]
    tweets_df['percent']=[round(classi['score'],4)*100 for classi in classifier(list(tweets_df['toenglish']))]

    logging.info(f"\n\n tweets df {tweets_df}")


    try:
        tweets_df.to_csv('tweetdata_updated.csv', index=True) 
    
    except "tweetdata_updated.csv file is already open" as e:
        logging.error("\n\n Please close the tweetdata_updated.csv file as it cannot write it and it will process only the old data")
        pass
   
if __name__ == "__main__":
    run()


