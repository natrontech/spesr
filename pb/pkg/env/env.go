package env

import (
	"log"

	"github.com/caarlos0/env/v8"
)

type config struct {
}

var Config config

func Init() {
	if err := env.Parse(&Config); err != nil {
		log.Printf("%+v\n", err)
	}
}
