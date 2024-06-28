package main

import (
	"log"
	"os"
	"path/filepath"
	"strings"

	"spesr/pkg/controller"
	"spesr/pkg/env"

	_ "spesr/docs" // import your generated docs

	"github.com/labstack/echo/v5"
	"github.com/pocketbase/pocketbase"
	"github.com/pocketbase/pocketbase/apis"
	"github.com/pocketbase/pocketbase/core"
	"github.com/pocketbase/pocketbase/plugins/jsvm"
	"github.com/pocketbase/pocketbase/plugins/migratecmd"

	tektonv1 "github.com/tektoncd/pipeline/pkg/apis/pipeline/v1"
)

// Dummy function to reference Tekton Types
func dummy() {
	var _ tektonv1.Pipeline
	var _ tektonv1.PipelineRun
	var _ tektonv1.Task
	var _ tektonv1.TaskRun
}

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
	dummy()
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

	app.OnBeforeServe().Add(func(e *core.ServeEvent) error {
		// serves static files from the provided public dir (if exists)
		e.Router.GET("/*", apis.StaticDirectoryHandler(os.DirFS(publicDirFlag), true))
		return nil
	})

	// custom endpoints
	app.OnBeforeServe().Add(func(e *core.ServeEvent) error {
		registerRoutes(e)
		return nil
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
	routes := []struct {
		Method      string
		Path        string
		Handler     echo.HandlerFunc
		Middlewares []echo.MiddlewareFunc
	}{
		{"GET", "/pb/avatar/:name", func(c echo.Context) error { return getAvatarHandler(c) }, []echo.MiddlewareFunc{}},
	}

	for _, route := range routes {
		e.Router.Add(route.Method, route.Path, route.Handler, route.Middlewares...)
	}
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
func getAvatarHandler(c echo.Context) error {
	name := c.PathParam("name")
	return controller.GetAvatar(c, name)
}
