El Portal de datos abiertos del Gobierno de Honduras ha sido desarrollado sobre [CKAN](https://ckan.org), un proyecto de código abierto usado por múltiples organizaciones en todo el mundo para publicar portales y plataformas de datos. Las personalizaciones específicas del portal del Gobierno de Honduras se pueden encontrar en [GitHub](https://github.com/datopian/ckanext-honduras).

Como todos los portales basados en CKAN, toda la funcionalidad del sitio puede ser accedida programáticamente mediante el uso de su API. La API ofrece acceso a todas las acciones que se pueden efectuar a través de la interfície de usuario. Se puede consultar la referéncia completa de la API en la [documentación oficial](https://docs.ckan.org/en/2.8/api/index.html) de CKAN, pero seguidamente se ofrece un resumen de sus características principales.

## Formato

La API de CKAN es de tipo [RPC](https://es.wikipedia.org/wiki/Llamada_a_procedimiento_remoto), donde se solicita una acción concreta, enviando si es necesario los datos requeridos para la llamada. El formato de intercanvio de la API es JSON.

La URL base de acceso a la API del portal es:

https://datos.gov.hn/api/3/

Por ejemplo para solicitar un listado de todas las categorias disponibles, usaremos la acción `group_list`:

    curl https://datos.gob.hn/api/3/action/group_list

    {
      "help": "https://datos.gob.hn/api/3/action/help_show?name=group_list",
      "result": [
          "medio-rural",
          "asuntos-internacionales",
          "ciencia-y-tecnologia",
          "economia",
          "educacion",
          "energia",
          "sector-publico",
          "legislacion-y-justicia",
          "medio-ambiente",
          "demografia",
          "sociedad-y-bienestar",
          "salud",
          "transporte"
      ],
      "success": true
    }

Para realizar busquedas en los metadatos de los datasets se utiliza la acción `package_search`:

    curl https://datos.gob.hn/api/3/action/package_search\?q\=res_format:CSV%20groups:medio-ambiente

    {
      "help": "https://datos.gob.hn/api/3/action/help_show?name=package_search",
      "success": true,
      "result": {
        "count": 9,
        "sort": "score desc, metadata_modified desc",
        "facets": {},
        "results": [
            ...
        ]
        "search_facets": {}

    }

El listado completo de acciones disponibles se puede consultar en la [documentación oficial](https://docs.ckan.org/en/2.8/api/index.html).

## Autorización

Algunas acciones en la API requieren que el usuario se identifique (por ejemplo acceso a datasets privados, creación o edición de datasets, etc). En ese caso es necesario proporcionar una clave de API en el encabezamiento `Authorization` de la solicitud, por ejemplo:

    curl -H Authorization:XXXX https://datos.gob.hn/api/3/action/package_show?id\=ejemplo-de-dataset-privado


Cada usuario registrado tiene una clave de API disponible. Se puede acceder a ella en la página del perfil de usuario en el portal, accesible haciendo clic en el nombre de usuario en la parte superior de la página:

![Clave API](https://raw.githubusercontent.com/datopian/ckanext-honduras/master/doc/claveapi.png)


