function euclideanDistance(pt1, pt2) {
    return Math.sqrt(Math.pow(pt1.x - pt2.x, 2) + Math.pow(pt1.y - pt2.y, 2));
}

export function HexGrid() {
    this.canvas = null;
    this.context = null;

    // Visual parameters
    this.zoom = 1;
    this.hexSize = 50;

    this.offset = {x: 0, y: 0};

    this.boardImages = [];    this.images = {};

    this.drawGrid = function () {
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

        this.context.stroke();
    };

    this.setCanvas = function (canvas) {
        this.canvas = canvas;
        this.canvas.width = 500;
        this.canvas.height = 500;
        this.context = this.canvas.getContext("2d");
    };

    this.update = function () {
        this.drawGrid();

        this.boardImages.forEach((obj) => {
            this.drawImage(obj.image, obj.x, obj.y);
        })
    };

    this.getCanvasFromCoordinates = function (x, y) {
        let xIncrement = this.hexSize * 0.866025;  // (sqrt(3) / 2)
        let yIncrement = this.hexSize * 1.5;

        let xBump = (x % 2) * xIncrement;
        return {
            x: xBump + x * (xIncrement * 2) + this.offset.x,
            y: y * yIncrement + this.offset.y + this.hexSize / 2
        };
    };

    this.drawImage = function (image, x, y) {
        let coords = this.getCanvasFromCoordinates(x, y);
        this.context.drawImage(this.images[image], coords.x - this.hexSize / 2, coords.y - this.hexSize / 2, this.hexSize, this.hexSize);
    };

    this.addImage = function (image, x, y) {
        this.boardImages.push({
            image: image,
            x: x,
            y: y
        });
    };

    this.mouseState = {
        prev: null,
        click: false,
        mouseDownPoint: null
    };

    this.setPrev = function (ev) {
        this.mouseState.prev = {
            x: ev.x,
            y: ev.y
        }
    };

    this.setOffset = function (pt1, pt2) {
        this.offset.x += pt2.x - pt1.x;
        this.offset.y += pt2.y - pt1.y;
    };

    this.handleMouseDown = function (ev) {
        let pt = {
            x: ev.clientX,
            y: ev.clientY
        };

        this.setPrev(ev);
        this.mouseState.mouseDownPoint = pt;
        this.mouseState.click = true;
    };

    this.handleMouseMove = function (ev) {
        if (!this.mouseState.click) return;
        let pt = {
            x: ev.clientX,
            y: ev.clientY
        };

        this.setOffset(this.mouseState.prev, pt);
        this.setPrev(ev);
    };

    this.handleMouseUp = function (ev) {
        this.mouseState.prev = null;
        this.mouseState.click = false;

        if (euclideanDistance(ev, this.mouseState.mouseDownPoint) < 10) {
            // Register this as a click instead of a drag.

        }
    };

    this.preloadImages = function () {
        let imgNames = ["ladybug", "queen"];

        imgNames.forEach((name) => {
            let img = new Image(); img.src = "static/images/" + name + ".png";
            this.images[name] = img;
        });

    }
}