# stalk-imvu
Herramienta de stalkeo en IMVU usando la API

El stalkeo consiste en revisar automáticamente las 40 últimas publicaciones de los seguidores de un usuario, y guarda un listado con las publicaciones en las que el usuario dio like, realizó un comentario, o aparece etiquetado.

Requiere de BD Mongo, y el ID de usuario a stalkear
Para uso de la API se requieren los datos de cookie en la sesión



El stalkeo se realiza en 3 fases principales:
## 1.- Recopilación de los seguidores del usuario
Es un proceso rápido y sencillo, guarda el ID de los seguidores en una colección de MongoDB

## 2.- Recopilación de los 40 últimos post de cada seguidor
Guarda los post en otra colección de Mongo, adicionalmente y de manera asíncrona obtiene el nombre asociado al ID del seguidor.

## 3.- Verificación de likes, comentarios, y tags
De manera asíncrona llama a 3 funciones para verificar la presencia de las interacciones en cada post.
Ésta fase es muy intensiva con la API de IMVU, ya que realiza 3 llamadas por cada post.

Si el usuario tiene 1,000 seguidores (el código está limitado a 1,500 seguidores), se recuperarán 40,000 posts (o tal vez menos), por lo que en total se realizarán poco más de 120,000 consultas a la API
