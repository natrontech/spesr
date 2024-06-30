/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("frv5fa0d678jb4c")

  collection.listRule = "@request.auth.id != \"\" && (@request.auth.id = user.id || @request.auth.role = \"admin\")"
  collection.viewRule = "@request.auth.id != \"\" && (@request.auth.id = user.id || @request.auth.role = \"admin\")"

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("frv5fa0d678jb4c")

  collection.listRule = "@request.auth.id != \"\" && (@request.auth.id = user.id || @request.auth.role = \"admin\")\n"
  collection.viewRule = "@request.auth.id != \"\" && (@request.auth.id = user.id || @request.auth.role = \"admin\")\n"

  return dao.saveCollection(collection)
})
