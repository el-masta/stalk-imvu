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

client = MongoClient('localhost', 27017)
db = client.imvu
seguidores = db.seguidores
publicaciones = db.publicaciones

susodicho='' # Id de usuario a stalkear


headers = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36"}
cookies = {''} # Aqui se arma el objeto de cookies

def paso1(target):
   #Encuentra seguidores
   url='https://api.imvu.com/profile/profile-user-'+target+'/subscriptions?limit=1500'
   respuesta=json.loads(requests.get(url).text)
   #for user in respuesta['denormalized'][url]['data']['items']:
   for user in respuesta['denormalized'][url]['data']['items']:
      seguidorid=user[79:]
      print ('Seguido:\t'+seguidorid+ ' agregado')
      seguidores.update_one({'_id':seguidorid},{'$set':{'_id':seguidorid}}, upsert=True )

def paso2():
   #Encuentra posts de los seguidores y los guarda en publicaciones

   # Recupera seguidores
   followers=seguidores.find({},{'_id':1})
   a=0
   b=0
   for follower in followers:
      target=follower['_id']
      a+=1
      guardarNombre(target)

      #guarda id de publicacion
      url='https://api.imvu.com/feed/feed-personal-'+target+'?limit=40'
      normalized='https://api.imvu.com/feed/feed-personal-'+target+'/elements'
      respuesta=json.loads(requests.get( url, headers=headers, cookies=cookies).text)
      for post in respuesta['denormalized'][normalized]['data']['items']:
         b+=1
         postid=post[72:]
         print ('Post ('+str(a)+'-'+str(b)+'):\t'+postid)
         publicaciones.update_one({'_id':postid},{'$set':{'_id':postid, 'user':target }}, upsert=True )

def paso3():
   # Recupera publicaciones
   posts=publicaciones.find({ 'checked' : {'$nin':[True] } },{'_id':1})
   a=0
   for post in posts:
      a+=1
      target=post['_id']
      print (str(a)+':\t'+target)
      #Encuentra likes y comentarios
      encontrarLikes(target)
      encontrarComentarios(target)
      encontrarTags(target)
      publicaciones.update_one({'_id':target},{'$set':{'checked':True}})
      
def encontrarLikes(idPost):
   url='https://api.imvu.com/feed_element/feed_element-'+idPost+'/liked_by/user-'+susodicho
   respuesta=json.loads(requests.get(url).text)
   if respuesta['status']=='success':
      print ('Like:\thttps://es.imvu.com/next/feed/feed_element-'+idPost+'/')
      publicaciones.update_one({'_id':idPost},{'$set':{'liked':True}})
         
def encontrarComentarios(idPost):
   normalized='https://api.imvu.com/feed_element/feed_element-'+idPost+'/comments?limit=100'
   respuesta=json.loads(requests.get(normalized).text)
   if respuesta['status']=='failure':
      publicaciones.delete_one({'_id':idPost})
   else:
      for comment in respuesta['denormalized'][normalized]['data']['items']:
         if respuesta['denormalized']['https://api.imvu.com/feed_comment/feed_comment-'+comment[106:]]['relations']['author'][31:]==susodicho:
            print ('Coment:\thttps://es.imvu.com/next/feed/feed_element-'+idPost+'/')
            publicaciones.update_one({'_id':idPost},{'$set':{'commented':True}})

def encontrarTags(idPost):
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
                  publicaciones.update_one({'_id':idPost},{'$set':{'tagged':True}})

def guardarNombre(user):
   target=user
   #Guarda nombre de usuario
   url='https://api.imvu.com/users/cid/'+target
   #s = requests.Session()
   respuesta=json.loads(requests.get( url, headers=headers, cookies=cookies).content)
   nombre=respuesta['denormalized'][url]['data']['avatarname']
   print ('Usuario:'+nombre )
   seguidores.update_one({'_id':target},{'$set':{'nombre':nombre}}, upsert=True )

def exportarLigas():
   f = open ('/home/mario/Escritorio/ligas.txt','w')
   comentarios=publicaciones.find({ 'commented' : True },{'_id':1, 'user':1} ).sort( 'user',pymongo.ASCENDING )
   likes=publicaciones.find({ 'liked' : True },{'_id':1,'user':1}).sort( 'user',pymongo.ASCENDING )
   tags=publicaciones.find({ 'tagged' : True },{'_id':1,'user':1}).sort( 'user',pymongo.ASCENDING )
   f.write('**** COMENTARIOS ****\n')
   user=''
   for comentario in comentarios:
      if user!=comentario['user']:
         user=comentario['user']
         nombre=seguidores.find_one({ '_id' : user },{'nombre':1})['nombre']
         f.write('\nA:\t'+nombre+' ('+user+')\n')
      url='https://es.imvu.com/next/feed/feed_element-'+comentario['_id']+'/'
      f.write(url+'\n')
      print('Comentario:\t'+url)
   f.write('\n\n**** LIKES ****\n')
   user=''
   for like in likes:
      if user!=like['user']:
         user=like['user']
         nombre=seguidores.find_one({ '_id' : user },{'nombre':1})['nombre']
         f.write('\nA:\t'+nombre+' ('+user+')\n')
      url='https://es.imvu.com/next/feed/feed_element-'+like['_id']+'/'
      f.write(url+'\n')
      print('Like:\t'+url)
   f.write('\n\n**** ETIQUETAS ****\n')
   user=''
   for tag in tags:
      if user!=tag['user']:
         user=tag['user']
         nombre=seguidores.find_one({ '_id' : user },{'nombre':1})['nombre']
         f.write('\nEn foto de:\t'+nombre+' ('+user+')\n')
      url='https://es.imvu.com/next/feed/feed_element-'+tag['_id']+'/'
      f.write(url+'\n')
      print('Tag:\t'+url)
   f.close()
      
paso1(susodicho)
paso2()
paso3()
exportarLigas()


