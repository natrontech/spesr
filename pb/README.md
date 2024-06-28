# Spesr

There are two flavors of the backend:

1. Standard release downloaded from https://github.com/pocketbase/pocketbase/releases. It even allows [extending with JavaScript](https://pocketbase.io/docs/js-overview/). This one is a good start, but if you want full control see next.
2. Custom compiled (`go build`), possibly with my customizations and perhaps yours too.

Out of the box, the project assumes #2 (custom compiled with my customizations).

## standard (official) release of pocketbase

Download from release archive from https://github.com/pocketbase/pocketbase/releases/latest, unzip it and place the `pocketbase` binary in this folder, and you're done.

## custom build

If you would like to extend PocketBase and use it as a framework then there is a `main.go` in this folder that you can customize and build using `go build` or do live development using `modd`.

See https://pocketbase.io/docs/use-as-framework/ for details.

# Setup

## Architecture

*tbd*

## Build

Assuming you have Go language tools installed ...

`go build`

If you don't have Go and don't want to install it, you can use docker-compose setup. Otherwise, your only choice is to download the binary from https://github.com/pocketbase/pocketbase/releases/latest, and placing it in this folder. But then you are limited to using JavaScript or configuration (but not Go-language customizations).

## Run migrations

Before you can run the actual backend, you must run the migrations using `./pocketbase migrate up` in the current directory. It will create appropriate schema tables/collections.

## Run the backend

You can run the PocketBase backend direct with `./pocketbase serve` or using `npm run backend` in the `sk` directory. Note that `npm run backend` it is included by default, but if you want the backend to also serve the frontend assets, then you must add the `--publicDir ../frontend/build` option. (Read more about this in [sk/package.json](../sk/package.json).)

## Docker

A highly recommended option is to run it inside a Docker container. A `Dockerfile` is included that builds a production Docker image. Also, a `docker-compose.yml` along with an _override_ file example are included, which should be used during development.

## Active development with `modd`

Finally, if you are going to actively develop using Go using PocketBase as a framework, then you probably want to use [modd](https://github.com/cortesi/modd), a development tool that rebuilds and restarts your Go binary everytime a source file changes (live reload on change). An basic `modd.conf` config file is included in this setup. You can run it by installing `modd` (`go install github.com/cortesi/modd/cmd/modd@latest`) and then running `modd`. All this is done automatically for you if you are using Docker.

# Schema (Collections)

With the 0.9 version of PocketBase, JavaScript auto-migrations as implemented. The JS files in `pb_migrations` can create/drop/modify collections and data. These are executed automatically by PocketBase on startup.

Not only that, they are also generated automatically whenever you change the schema! So go ahead and make changes to the schema and watch new JS files generated in the `pb_migrations` folder. Just remember to commit them to version control.

## Generated Types

The file `generated-types.ts` contains TypeScript definitions of `Record` types mirroring the fields in your database collections. But it needs to be regenerated every time you modify the schema. This can be done by simply running the `typegen` script in the frontend's `package.json`. So remember to do that.

# OpenApi

Get the https://github.com/swaggo/swag CLI tool and run the following command to generate the OpenAPI documentation:

```bash
go install github.com/swaggo/swag/cmd/swag@latest
```

Then run:

```bash
swag init --parseDependency --parseInternal --output docs/
```