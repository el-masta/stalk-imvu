#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Revision de likes y comentarios en post de imvu
#  recupera y guarda datos de Mongo

import pymongo
from pymongo import MongoClient
import requests
from requests.auth import HTTPBasicAuth
import json
import concurrent.futures

client = MongoClient('localhost', 27017)
db = client.imvu
seguidores = db.cseguidores
publicaciones = db.cpublicaciones

susodicho='' # ID de usuario IMVU a stalkear

headers = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36"}
cookies = {''} # Aqui se arma el diccionario de cookies

def encontrarSeguidores(target):
   '''Encuentra seguidores'''
   url='https://api.imvu.com/profile/profile-user-'+target+'/subscriptions?limit=1500'
   respuesta=json.loads(requests.get(url).text)
   for user in respuesta['denormalized'][url]['data']['items']:
      seguidorid=user[79:]
      res=seguidores.find_one({ '_id' : seguidorid },{'nombre':1})
      if res!=None:
         print('Usuario saltado ya revisado')
      else:
         seguidores.update_one({'_id':seguidorid},{'$set':{'_id':seguidorid,'rank':0}}, upsert=True )
         with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor1:
            executor1.map( guardarNombre(seguidorid) )
            executor1.map( encontrarPosts(seguidorid) )
         print ('Seguido:\t'+seguidorid+ ' agregado')
      res= None


def guardarNombre(user):
   '''Guarda nombre de usuario'''
   url='https://api.imvu.com/users/cid/'+user
   respuesta=json.loads(requests.get( url, headers=headers, cookies=cookies).content)
   nombre=respuesta['denormalized'][url]['data']['avatarname']
   print ('Usuario:'+nombre )
   seguidores.update_one({'_id':user},{'$set':{'nombre':nombre}}, upsert=True )

def encontrarPosts(target):
   '''Encuentra los posts'''
   url='https://api.imvu.com/feed/feed-personal-'+target+'?limit=40'
   normalized='https://api.imvu.com/feed/feed-personal-'+target+'/elements'
   respuesta=json.loads(requests.get( url, headers=headers, cookies=cookies).text)
   b=0
   print( str(len(respuesta['denormalized'][normalized]['data']['items']))+' posts' )
   for post in respuesta['denormalized'][normalized]['data']['items']:
      b+=1
      postid=post[72:]
      print ('Post ('+str(b)+'):\t'+postid)
      explorarPosts(postid,target)

def explorarPosts(postid,target):
   '''Explora cada uno de los posts buscando likes, comentarios y etiquetas'''
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor2:
      executor2.map( encontrarLikes(postid,target) )
      executor2.map( encontrarComentarios(postid,target) )
      executor2.map( encontrarTags(postid,target) )
      
def encontrarLikes(idPost,target):
   url='https://api.imvu.com/feed_element/feed_element-'+idPost+'/liked_by/user-'+susodicho
   respuesta=json.loads(requests.get(url).text)
   if respuesta['status']=='success':
      print ('Like:\thttps://es.imvu.com/next/feed/feed_element-'+idPost+'/')
      publicaciones.update_one({'_id':idPost},{'$set':{'_id':idPost,'liked':True,'user':target}}, upsert=True )
      seguidores.update_one({'_id':target},{'$inc':{'rank':1}}, upsert=True )
         
def encontrarComentarios(idPost,target):
   normalized='https://api.imvu.com/feed_element/feed_element-'+idPost+'/comments?limit=100'
   respuesta=json.loads(requests.get(normalized).text)
   if respuesta['status']=='failure':
      pass
   else:
      for comment in respuesta['denormalized'][normalized]['data']['items']:
         if respuesta['denormalized']['https://api.imvu.com/feed_comment/feed_comment-'+comment[106:]]['relations']['author'][31:]==susodicho:
            print ('Coment:\thttps://es.imvu.com/next/feed/feed_element-'+idPost+'/')
            publicaciones.update_one({'_id':idPost},{'$set':{'commented':True,'user':target}}, upsert=True )
            seguidores.update_one({'_id':target},{'$inc':{'rank':1}}, upsert=True )

def encontrarTags(idPost,target):
   urlPost='https://api.imvu.com/feed_element/feed_element-'+idPost
   respuesta=json.loads(requests.get(urlPost).text)
   if respuesta['status']=='success':
      if 'photo_details' in respuesta['denormalized'][urlPost]['relations']:
         urlDetallesFoto=respuesta['denormalized'][urlPost]['relations']['photo_details']
         respuesta=json.loads(requests.get(urlDetallesFoto, headers=headers, cookies=cookies).content)
         if respuesta['status']=='success':
            for tag in respuesta['denormalized']:
               if tag[31:]==susodicho:
                  print ('Tag:\thttps://es.imvu.com/next/feed/feed_element-'+idPost+'/')
                  publicaciones.update_one({'_id':idPost},{'$set':{'_id':idPost, 'tagged':True,'user':target}}, upsert=True )
                  seguidores.update_one({'_id':target},{'$inc':{'rank':1}}, upsert=True )

def exportarLigas():
   f = open ('~/Escritorio/ligas.txt','w')
   followers=seguidores.find({'rank':{'$gt':0}},{'_id':1,'nombre':1}).sort( 'rank',pymongo.DESCENDING )
   for seguidor in followers:
      print('\nCon usuario: '+seguidor['nombre'])
      f.write('\nCon usuario: '+seguidor['nombre']+'\n')
      pubs=publicaciones.find({ 'user' : seguidor['_id'] }).sort( 'user',pymongo.ASCENDING )
      for pub in pubs:
         linea='https://es.imvu.com/next/feed/feed_element-'+pub['_id']+'/    '
         if 'liked' in pub:
            linea+='Like '
         else:
            linea+='     '
         if 'commented' in pub:
            linea+='Comentario '
         else:
            linea+='           '
         if 'tagged' in pub:
            linea+='Etiqueta '
         print(linea)
         f.write(linea+'\n')
   f.close()
   
encontrarSeguidores(susodicho)
exportarLigas()
