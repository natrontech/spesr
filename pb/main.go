package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"spesr/pkg/controller"
	"spesr/pkg/env"

	"github.com/pocketbase/pocketbase"
	"github.com/pocketbase/pocketbase/apis"
	"github.com/pocketbase/pocketbase/core"
	"github.com/pocketbase/pocketbase/plugins/jsvm"
	"github.com/pocketbase/pocketbase/plugins/migratecmd"
	"github.com/pocketbase/pocketbase/tools/hook"
)

// @title Flexmox API
// @version 1.0
// @description Flexmox API
// @contact.name Natron Tech AG
// @contact.url https://natron.io
// @contact.email support@natron.io
// @host localhost:8090
// @BasePath /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
func main() {
	app := pocketbase.New()

	var publicDirFlag string

	// add "--publicDir" option flag
	app.RootCmd.PersistentFlags().StringVar(
		&publicDirFlag,
		"publicDir",
		defaultPublicDir(),
		"the directory to serve static files",
	)

	migrationsDir := ""

	// load js files to allow loading external JavaScript migrations
	jsvm.MustRegister(app, jsvm.Config{
		MigrationsDir: migrationsDir,
	})

	// register the `migrate` command
	migratecmd.MustRegister(app, app.RootCmd, migratecmd.Config{
		TemplateLang: migratecmd.TemplateLangJS, // or migratecmd.TemplateLangGo (default)
		Dir:          migrationsDir,
		Automigrate:  true,
	})

	app.OnServe().BindFunc(func(e *core.ServeEvent) error {
		registerRoutes(e)
		return e.Next()
	})

	// Register the SPA fallback after application routes.
	app.OnServe().Bind(&hook.Handler[*core.ServeEvent]{
		Func: func(e *core.ServeEvent) error {
			if !e.Router.HasRoute(http.MethodGet, "/{path...}") {
				e.Router.GET("/{path...}", apis.Static(os.DirFS(publicDirFlag), true))
			}
			return e.Next()
		},
		Priority: 999,
	})

	if err := app.Start(); err != nil {
		log.Fatal(err)
	}
}

func defaultPublicDir() string {
	if strings.HasPrefix(os.Args[0], os.TempDir()) {
		// most likely ran with go run
		return "./pb_public"
	}

	return filepath.Join(os.Args[0], "../pb_public")
}

func init() {
	env.Init()
}

// registerRoutes registers all routes for the application
func registerRoutes(e *core.ServeEvent) {
	e.Router.GET("/pb/avatar/{name}", getAvatarHandler)
}

// @Summary Get Avatar
// @Description Get an avatar by name
// @Tags Avatar
// @Produce png
// @Param name path string true "Avatar Name"
// @Success 200 {string} binary "Returns the generated avatar image"
// @Failure 400 {object} map[string]interface{} "Invalid request"
// @Failure 500 {object} map[string]interface{} "Internal server error"
// @Router /pb/avatar/{name} [get]
func getAvatarHandler(e *core.RequestEvent) error {
	return controller.GetAvatar(e, e.Request.PathValue("name"))
}
