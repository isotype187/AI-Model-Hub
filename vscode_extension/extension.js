const vscode = require("vscode");
const fs = require("fs");
const path = require("path");

const ROOT = "D:/AI_Model_Hub";
const REQUEST_DIR = path.join(ROOT, "bridge", "requests");
const RESPONSE_DIR = path.join(ROOT, "bridge", "responses");

function log(message) {
    console.log("[AI Hub Bridge] " + message);
}

function processTask(file) {

    const task = JSON.parse(
        fs.readFileSync(file, "utf8")
    );

    log("Processing " + task.task_id);

    const response = {
        task_id: task.task_id,
        completed: new Date().toISOString(),
        status: "completed",
        result: "VS Code extension received task successfully."
    };

    fs.writeFileSync(
        path.join(RESPONSE_DIR, task.task_id + ".json"),
        JSON.stringify(response, null, 4)
    );

    fs.unlinkSync(file);
}

function activate(context) {

    log("Extension activated");

    fs.mkdirSync(REQUEST_DIR, { recursive: true });
    fs.mkdirSync(RESPONSE_DIR, { recursive: true });

    fs.watch(REQUEST_DIR, () => {

        const files = fs.readdirSync(REQUEST_DIR);

        for (const file of files) {

            if (file.endsWith(".json")) {

                try {

                    processTask(
                        path.join(REQUEST_DIR, file)
                    );

                } catch (err) {

                    console.error(err);

                }

            }

        }

    });

}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
