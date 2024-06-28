/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "7huq9rbs25jyrwv",
    "created": "2024-06-29 12:11:58.210Z",
    "updated": "2024-06-29 12:11:58.210Z",
    "name": "customers",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "h6izurvc",
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
  const collection = dao.findCollectionByNameOrId("7huq9rbs25jyrwv");

  return dao.deleteCollection(collection);
})
