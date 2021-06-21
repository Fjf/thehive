function mod(n, m) {
    return ((n % m) + m) % m;
}

function euclideanDistance(pt1, pt2) {
    return Math.sqrt(Math.pow(pt1.x - pt2.x, 2) + Math.pow(pt1.y - pt2.y, 2));
}

function getCanvasMouseCoordinates(canvas, ev) {
    const rect = canvas.getBoundingClientRect();
    const {width, height} = canvas.getBoundingClientRect();
    return {
        x: (ev.x - rect.left) * (canvas.width / width),
        y: (ev.y - rect.top) * (canvas.height / height)
    };
}

function isInCanvas(canvas, ev) {
    let pt = getCanvasMouseCoordinates(canvas, ev);
    return pt.x >= 0 && pt.y >= 0 && pt.x < canvas.width && pt.y < canvas.height
}


function Point(x, y) {
    this.x = x;
    this.y = y;
}

export function HexGrid() {
    this.canvas = null;
    this.context = null;

    // Visual parameters
    this.zoom = 1;
    this.hexSize = 50;
    this.tileHeight = 15;

    this.offset = {x: 0, y: 0};

    this.boardState = {};
    this.markedTiles = [];

    this.images = {};
    this.audio_files = {};

    this.tileColour = "#f5e8cb";
    this.tileEdgeColour = "#5e594d";

    this.remoteTileColour = "#5e594d";
    this.remoteTileEdgeColour = "#f5e8cb";

    this.onTilePlaceHandler = null;
    this.onTilePickupHandler = null;

    this.selection = null;
    this.player1 = null;
    this.player2 = null;
    this.username = null;

    this.setBoardState = function(data) {
        this.boardState = {};
        for (const [y, row] of Object.entries(data)) {
            for (const [x, values] of Object.entries(row)) {
                let tile;

                let z = 0;
                for (let val of values) {
                    if (val.image === null) continue;

                    tile = this.makeTile(val.image, x, y, this.tileClickHandler);
                    tile.number = val.number;
                    tile.color = val.color;
                    tile.z = z++;

                    this.putTile(tile, x, y);
                }
            }
        }
    };

    this.drawGrid = function() {
        if (this.context == null) return;

        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Do horizontal lines
        this.context.beginPath();

        let xIncrement = this.hexSize * 0.866025;  // (sqrt(3) / 2)
        let yIncrement = this.hexSize * 1.5;

        // Zigzag lines
        for (let y = -3; y < this.canvas.height / yIncrement + 3; y++) {
            let yPos = y * yIncrement + (this.offset.y % (2 * yIncrement));

            this.context.moveTo(-1, yPos - (y % 2) * (this.hexSize / 2));
            for (let x = -3; x < this.canvas.width / xIncrement + 3; x++) {
                let xPos = x * xIncrement + (this.offset.x % (xIncrement * 2));
                if ((x + y) % 2 === 0) {
                    this.context.lineTo(xPos, yPos - this.hexSize / 2);
                } else {
                    this.context.lineTo(xPos, yPos);
                }
            }
        }

        let verticalHeight = yIncrement - this.hexSize / 2;
        // Vertical lines
        for (let y = -3; y < this.canvas.height / yIncrement + 3; y++) {
            let yPos = y * yIncrement + (this.offset.y % (yIncrement * 2));
            for (let x = -3; x < this.canvas.width / xIncrement + 3; x += 2) {
                let xPos = x * xIncrement + (this.offset.x % (xIncrement * 2));
                if ((x + y) % 2 === 0) {
                    this.context.moveTo(xPos + xIncrement, yPos);
                    this.context.lineTo(xPos + xIncrement, yPos + verticalHeight);
                } else {
                    this.context.moveTo(xPos, yPos);
                    this.context.lineTo(xPos, yPos + verticalHeight);
                }
            }
        }

        this.context.strokeStyle = "black";
        this.context.lineJoin = "miter";
        this.context.lineWidth = "2";
        this.context.stroke();
    };

    this.setCanvas = function(canvas) {
        this.canvas = canvas;
        this.canvas.width = 1000;
        this.canvas.height = 800;
        this.context = this.canvas.getContext("2d");
        this.context.translate(0.5, 0.5);
    };

    this.update = function() {
        this.drawGrid();

        // TODO: check performance of dictionary querying.
        for (const [y, row] of Object.entries(this.boardState)) {
            for (const [x, values] of Object.entries(row)) {
                for (let tile of values) {
                    let pos = this.getCanvasFromCoordinates(x, y);
                    this.drawTile(tile, pos.x, pos.y);
                }
            }
        }

        // Draw available tiles
        for (let entry of this.markedTiles) {
            this.markAvailable(entry[0], entry[1], 0);
        }

        if (this.selection !== null) {
            // Always draw selected tile on top of everything.
            this.drawTile(this.selection, this.mouseState.pos.x, this.mouseState.pos.y);
        }

        if (this.enemyMouseState.pos !== null) {
            this.drawTile(this.enemyMouseState.tile, this.enemyMouseState.pos.x + this.offset.x, this.enemyMouseState.pos.y + this.offset.y)
        }

        if (this.mouseState.tile !== null) {
            this.drawTile(this.mouseState.tile, this.mouseState.pos.x + this.offset.x, this.mouseState.pos.y + this.offset.y)
        }
    };

    this.getCanvasFromCoordinates = function(x, y) {
        let xIncrement = this.hexSize * 0.866025;  // (sqrt(3) / 2)
        let yIncrement = this.hexSize * 1.5;

        let xBump = -(y * xIncrement);
        return {
            x: xBump + x * (xIncrement * 2) + this.offset.x,
            y: y * yIncrement + this.offset.y + this.hexSize / 2
        };
    };

    this.drawImage = function(image, x, y) {
        let coords = this.getCanvasFromCoordinates(x, y);
        this.context.drawImage(this.images[image], coords.x - this.hexSize / 2, coords.y - this.hexSize / 2, this.hexSize, this.hexSize);
    };

    this.makeTile = function(image, x, y, onclickCallback) {
        return {x: x, y: y, z: 0, image: image, callback: onclickCallback, mine: true};
    };

    this.enemyMouseState = {
        pos: null,
        tile: null
    };

    this.setEnemyHover = function(data) {
        if (data !== undefined) {
            this.enemyMouseState.pos = data.pos;
            this.enemyMouseState.tile = data.tile;
        } else {
            this.enemyMouseState.pos = null;
        }
    };

    this.setHover = function(data) {
        if (data !== undefined) {
            this.mouseState.pos = data.pos;
            this.mouseState.tile = data.tile;
        } else {
            this.mouseState.pos = null;
            this.mouseState.tile = null;
        }
    };

    this.addObject = function(image, x, y, onclickCallback) {
        let tile = this.makeTile(image, x, y, onclickCallback);
        this.putTile(tile, x, y);
    };

    this.mouseState = {
        prev: null,
        click: false,
        mouseDownPoint: null,
        pos: null,
        tile: null
    };

    this.select = function(name) {
        this.selection = this.makeTile(name, null, null, this.tileClickHandler);
        this.selection.owner = this.username;
    };

    this.setPrev = function(ev) {
        this.mouseState.prev = {
            x: ev.x,
            y: ev.y
        }
    };

    this.setPos = function(ev) {
        this.mouseState.pos = getCanvasMouseCoordinates(this.canvas, ev);
    };

    this.setOffset = function(pt1, pt2) {
        this.offset.x += pt2.x - pt1.x;
        this.offset.y += pt2.y - pt1.y;
    };

    this.isPlayer = function() {
        return this.username === this.player1 || this.username === this.player2;
    };

    this.handleMouseDown = function(ev) {
        if (!this.isPlayer()) return;
        if (!isInCanvas(this.canvas, ev)) return;

        let pt = {
            x: ev.x,
            y: ev.y
        };


        this.setPrev(ev);
        this.setPos(ev);
        this.mouseState.mouseDownPoint = pt;
        this.mouseState.click = true;
    };

    this.handleMouseMove = function(ev) {
        if (!this.isPlayer()) return;

        this.setPos(ev);

        if (!this.mouseState.click) return;
        let pt = {
            x: ev.clientX,
            y: ev.clientY
        };
        this.setOffset(this.mouseState.prev, pt);
        this.setPrev(ev);
    };

    this.getTile = function(x, y) {
        if (this.boardState[y] !== undefined &&
            this.boardState[y][x] !== undefined &&
            this.boardState[y][x].length > 0)
        {
            return this.boardState[y][x][this.boardState[y][x].length - 1];
        }
        return null;
    };

    this.removeTile = function(x, y) {
        if (this.boardState[y] !== undefined && this.boardState[y][x] !== undefined) {
            this.boardState[y][x].pop();
        }
    };

    this.putTile = function(tile, x, y) {
        if (this.boardState[y] === undefined) this.boardState[y] = {};
        if (this.boardState[y][x] === undefined) this.boardState[y][x] = [];
        tile.x = x;
        tile.y = y;
        tile.z = this.boardState[y][x].length;
        this.boardState[y][x].push(tile);
    };

    this.tileClickHandler = function(self, ev, tile) {
        // Local onclick handler for tiles.
        // E.g. sound files can be played here.
    };

    this.getClosestHexagon = function(ev) {
        // TODO: Optimize this to look at less hexagons instead.
        let xIncrement = this.hexSize * 0.866025;  // (sqrt(3) / 2)
        let yIncrement = this.hexSize * 1.5;

        let cvs = getCanvasMouseCoordinates(this.canvas, ev);

        // var xBump = -(y * xIncrement);
        // return {
        //     x: xBump + x * (xIncrement * 2) + this.offset.x,
        //     y: y * yIncrement + this.offset.y + this.hexSize / 2
        let yCenter = Math.round((cvs.y - this.offset.y - this.hexSize) / yIncrement);
        let xCenter = Math.round((cvs.x - this.offset.x + (yCenter * xIncrement)) / (xIncrement * 2));
        // y: y * yIncrement + this.offset.y + this.hexSize / 2
        // Check of the two upper neighbours, and this point, which center point is the closest.
        let points = this.getSurroundingArea(new Point(xCenter, yCenter));
        let canvasPoints = [];
        points.forEach((point) => {
            let pt = this.getCanvasFromCoordinates(point.x, point.y);
            canvasPoints.push(pt);
        });

        let closest = points[0];
        let minDist = euclideanDistance(closest, cvs);

        canvasPoints.forEach((point) => {
            let dist = euclideanDistance(point, cvs);
            if (dist < minDist) {
                minDist = dist;
                closest = point;
            }
        });

        // Doing +0.5 then Math.floor makes sure we never get -0.
        let y = Math.floor((closest.y - this.offset.y) / yIncrement + 0.5);
        let x = Math.floor((closest.x - this.offset.x + y * xIncrement) / (xIncrement * 2) + 0.5);
        return {
            x: x,
            y: y
        };
    };

    this.setP1TileStyle = function() {
        this.context.strokeStyle = this.tileEdgeColour;
        this.context.lineJoin = "round";
        this.context.lineWidth = "4";
        this.context.fillStyle = this.tileColour;
    };

    this.setP2TileStyle = function() {
        this.context.strokeStyle = this.remoteTileEdgeColour;
        this.context.lineJoin = "round";
        this.context.lineWidth = "4";
        this.context.fillStyle = this.remoteTileColour;
    };

    this.markAvailable = function(x, y, z) {
        let pt = this.getCanvasFromCoordinates(x, y);

        this.setP1TileStyle();
        this.context.beginPath();
        this.context.arc(pt.x, pt.y - (z * this.tileHeight), this.hexSize / 2, 0, Math.PI * 2);
        this.context.stroke();
        this.context.fill();
    };

    this.handleMouseUp = function(ev) {
        if (!this.isPlayer()) return;

        if (this.mouseState.mouseDownPoint === null) return;

        this.mouseState.prev = null;
        this.mouseState.click = false;

        if (euclideanDistance(ev, this.mouseState.mouseDownPoint) < 10) {
            // Register this as a click instead of a drag.
            let point = this.getClosestHexagon(ev);
            if (this.selection === null) {
                // If no tile is yet selected, select the currently hovering tile.
                let tile = this.getTile(point.x, point.y);
                if (tile !== null && tile.mine) {
                    tile.callback(this, ev, tile);
                    this.onTilePickupHandler(tile);
                }
            } else {
                // Try to deselect currently selected tile and place on hovering tile.
                this.selection.new_x = point.x;
                this.selection.new_y = point.y;
                // Cannot place immediately, because server needs to validate position is valid first.
                // this.putTile(this.selection, point.x, point.y);
                this.onTilePlaceHandler(this.selection);
            }
        }
    };

    this.drawTile = function(tile, x, y) {
        let xIncrement = this.hexSize * 0.866025;  // (sqrt(3) / 2)

        let xStart = x - xIncrement;
        let yStart = y - this.hexSize / 2;

        let tileThickness = this.tileHeight;

        if (tile.color === 0)
            this.setP1TileStyle();
        else
            this.setP2TileStyle();

        this.context.beginPath();
        this.context.moveTo(xStart, yStart - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + xIncrement, yStart - 0.5 * this.hexSize - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + 2 * xIncrement, yStart - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + 2 * xIncrement, yStart + this.hexSize - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + xIncrement, yStart + 1.5 * this.hexSize - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart, yStart + this.hexSize - tileThickness * (tile.z + 1));
        this.context.closePath();
        this.context.stroke();
        this.context.fill();

        // 3d effect.
        this.context.beginPath();
        this.context.moveTo(xStart + 2 * xIncrement, yStart + this.hexSize - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + 2 * xIncrement, yStart + this.hexSize - tileThickness * tile.z);
        this.context.lineTo(xStart + xIncrement, yStart + 1.5 * this.hexSize - tileThickness * tile.z);
        this.context.lineTo(xStart, yStart + this.hexSize - tileThickness * tile.z);
        this.context.lineTo(xStart, yStart + this.hexSize - tileThickness * (tile.z + 1));
        this.context.lineTo(xStart + xIncrement, yStart + 1.5 * this.hexSize - tileThickness * (tile.z + 1));
        this.context.closePath();
        this.context.stroke();
        this.context.fill();

        let s = this.hexSize / 2;
        this.context.drawImage(this.images[tile.image],
            x - s, y - s - tileThickness * (tile.z + 1), this.hexSize, this.hexSize);
    };

    this.getNeighbours = function(point) {
        let points = [];
        // Left and right
        points.push(new Point(point.x - 1, point.y));
        points.push(new Point(point.x + 1, point.y));

        // Top and bottom
        points.push(new Point(point.x, point.y - 1));
        points.push(new Point(point.x, point.y + 1));

        // The other top and bottom
        points.push(new Point(point.x - 1, point.y - 1));
        points.push(new Point(point.x + 1, point.y + 1));
        return points;
    };

    this.getSurroundingArea = function(point) {
        // Center
        let points = this.getNeighbours(point);
        points.push(new Point(point.x, point.y));

        return points;
    };

    this.preloadResources = function(initialTileNames) {
        initialTileNames.forEach((tileName) => {
            let img = new Image();
            img.src = "static/images/" + tileName.name + ".png";
            this.images[tileName.name] = img;
        });

        let audioNames = ["tile_sound_1", "tile_sound_2", "success", "incorrect"];
        audioNames.forEach((name) => {
            this.audio_files[name] = new Audio("static/audio/" + name + ".mp3");
        })
    }
}