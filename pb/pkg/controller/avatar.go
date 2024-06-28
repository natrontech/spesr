package controller

import (
	"bytes"
	"crypto/md5"
	"encoding/hex"
	"image/color"
	"net/http"
	"strconv"

	"github.com/fogleman/gg"
	"github.com/labstack/echo/v5"
)

func generateGradientAvatar(name string) ([]byte, error) {
	// Generate hash from name
	hash := md5.Sum([]byte(name))
	hexColor := hex.EncodeToString(hash[:])

	// Create gradient colors from the hash
	color1 := color.RGBA{
		R: hexToByte(hexColor[0:2]),
		G: hexToByte(hexColor[2:4]),
		B: hexToByte(hexColor[4:6]),
		A: 255,
	}

	// Additional color to add more uniqueness
	color3 := color.RGBA{
		R: hexToByte(hexColor[12:14]),
		G: hexToByte(hexColor[14:16]),
		B: hexToByte(hexColor[16:18]),
		A: 255,
	}

	// Create a new image with gradient
	const size = 128
	dc := gg.NewContext(size, size)
	grad := gg.NewLinearGradient(0, 0, float64(size), float64(size))
	grad.AddColorStop(0, color1)
	grad.AddColorStop(1, color3)
	dc.SetFillStyle(grad)
	dc.DrawRectangle(0, 0, size, size)
	dc.Fill()

	// Encode the image to PNG
	var buf bytes.Buffer
	err := dc.EncodePNG(&buf)
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func hexToByte(hexStr string) uint8 {
	val, _ := strconv.ParseUint(hexStr, 16, 8)
	return uint8(val)
}

func GetAvatar(c echo.Context, name string) error {
	img, err := generateGradientAvatar(name)
	if err != nil {
		return c.String(http.StatusInternalServerError, "Failed to generate avatar")
	}

	return c.Blob(http.StatusOK, "image/png", img)
}
