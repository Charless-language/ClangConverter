package main

import (
	"fmt"
	"io/ioutil"
	"os"

	"charless-converter/pkg/transpiler"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Printf("Usage: %s <input.cless> <output.c>\n", os.Args[0])
		os.Exit(1)
	}

	inputFile := os.Args[1]
	outputFile := os.Args[2]

	content, err := ioutil.ReadFile(inputFile)
	if err != nil {
		fmt.Printf("Error reading file: %v\n", err)
		os.Exit(1)
	}

	trans := transpiler.NewTranspiler()
	res, err := trans.Transpile(string(content))
	if err != nil {
		fmt.Printf("Transpilation error: %v\n", err)
		os.Exit(1)
	}

	err = ioutil.WriteFile(outputFile, []byte(res), 0644)
	if err != nil {
		fmt.Printf("Error writing output: %v\n", err)
		os.Exit(1)
	}
}
