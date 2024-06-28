/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("frv5fa0d678jb4c")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "0zt4dfjy",
    "name": "user",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "collectionId": "_pb_users_auth_",
      "cascadeDelete": false,
      "minSelect": null,
      "maxSelect": 1,
      "displayFields": null
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("frv5fa0d678jb4c")

  // remove
  collection.schema.removeField("0zt4dfjy")

  return dao.saveCollection(collection)
})
