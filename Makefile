APP_NAME = charless-converter
VERSION = 1.0.0
ARCH = amd64
PKG_DIR = package

.PHONY: all build clean package

all: clean build package

build:
	mkdir -p bin
	go build -o bin/c2charless ./cmd/c2charless
	go build -o bin/charless2c ./cmd/charless2c

package:
	mkdir -p $(PKG_DIR)/DEBIAN
	mkdir -p $(PKG_DIR)/usr/local/bin
	cp bin/c2charless $(PKG_DIR)/usr/local/bin/
	cp bin/charless2c $(PKG_DIR)/usr/local/bin/
	# Create control file
	echo "Package: $(APP_NAME)" > $(PKG_DIR)/DEBIAN/control
	echo "Version: $(VERSION)" >> $(PKG_DIR)/DEBIAN/control
	echo "Section: devel" >> $(PKG_DIR)/DEBIAN/control
	echo "Priority: optional" >> $(PKG_DIR)/DEBIAN/control
	echo "Architecture: $(ARCH)" >> $(PKG_DIR)/DEBIAN/control
	echo "Maintainer: Charless Dev <dev@example.com>" >> $(PKG_DIR)/DEBIAN/control
	echo "Description: Charless C to Bytecode Converter" >> $(PKG_DIR)/DEBIAN/control
	echo " Tools to convert C subset to Charless bytecode and back." >> $(PKG_DIR)/DEBIAN/control
	
	chmod 755 $(PKG_DIR)/DEBIAN
	chmod 755 $(PKG_DIR)/DEBIAN/control
	chmod 755 $(PKG_DIR)/usr/local/bin/c2charless
	chmod 755 $(PKG_DIR)/usr/local/bin/charless2c
	
	dpkg-deb --build $(PKG_DIR) $(APP_NAME)_$(VERSION)_$(ARCH).deb

clean:
	rm -rf bin $(PKG_DIR) *.deb
