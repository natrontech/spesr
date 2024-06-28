/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "7xzqxa4a17wgr05",
    "created": "2024-06-29 12:12:26.098Z",
    "updated": "2024-06-29 12:12:26.098Z",
    "name": "expense_types",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "7wssejnj",
        "name": "name",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
        }
      }
    ],
    "indexes": [],
    "listRule": null,
    "viewRule": null,
    "createRule": null,
    "updateRule": null,
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("7xzqxa4a17wgr05");

  return dao.deleteCollection(collection);
})
