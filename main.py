from youtube_search import YoutubeSearch
from threading import Thread
from base64 import b64encode
import youtube_dl
import requests
import os

# declare globals
results = {}

def refresh_token():
  clientID = os.environ['clientID']
  clientSecret = os.environ['clientSecret']
  data = f"{clientID}:{clientSecret}"
  headers = {'Authorization': f'Basic {b64encode(data.encode()).decode()}'}
  data = requests.post('https://accounts.spotify.com/api/token', data={'grant_type': 'client_credentials'}, headers=headers)
  return data.json()['access_token']
  
def query_term(term):
  token = f'Bearer {refresh_token()}'
  headers = {}
  for item in open('headers.txt','r').read().split('\n'):
    if item.split(':')[0] == 'authorization':
      headers['Authorization'] = token
    else:
      headers[item.split(':')[0]] = item.split(':')[1][1:]
  request = requests.get(f'https://api.spotify.com/v1/search?q={term}&type=track', headers=headers)
  request = request.json()['tracks']['items']
  results = {}

  for i, item in enumerate(request):
    if item['album']['album_type'] == 'single':
      name = item['album']['name']
      artist = item['album']['artists'][0]['name']
      thumbnail = item['album']['images'][0]['url']
      
      results[i] = {
        'name': name,
        'artist': artist,
        'thumbnail': thumbnail
      }
    else:
      # indexes album for song
      if item['album']['album_type'] == 'album':
        album_url = item['album']['href']
        request = requests.get(album_url, headers=headers)
        for song in request.json()['tracks']['items']:
          # uses threading for faster searching
          Thread(target=lambda: query_song(song, term, i, headers))
  return results

def query_song(data, term, i, headers):
  name = song['name']
  artist = song['artists'][0]['name']
  request = requests.get(song['href'], headers=headers)
  thumbnail = request.json()['album']['images'][0]['url']
  if term.lower() in name.lower():
    results[i] = {
      'name': name,
      'artist': artist,
      'thumbnail': thumbnail
    }
  
def top_query_term(term):
  items = query_term(term)
  return items[list(items.keys())[0]]

song = top_query_term('search query')
results = YoutubeSearch(f"{song['artist']} {song['name']}", max_results=1).to_dict()
video_info = youtube_dl.YoutubeDL().extract_info(url=f'https://www.youtube.com/watch?v={results[0]["id"]}', download=False)

options={
  'format': 'bestaudio/best',
  'keepvideo': False,
  'outtmpl': 'song.mp3'
  }

with youtube_dl.YoutubeDL(options) as ydl:
  ydl.download([video_info['webpage_url']])
