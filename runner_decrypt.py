import frida, time, sys, os

def on_message(message, data):
    if message.get('type') == 'send':
        print(f"[Frida] {message.get('payload')}")
    elif message.get('type') == 'error':
        print(f"[Frida Error] {message.get('description')}")
    else:
        print(f"[Frida Msg] {message}")

device = frida.get_usb_device()
print("[*] Spawning com.indomaret.klikindomaret under Frida control...")
pid = device.spawn(["com.indomaret.klikindomaret"])
session = device.attach(pid)

js_code = """
function initHarvester() {
    if (typeof Java === 'undefined' || !Java.available) {
        setTimeout(initHarvester, 50);
        return;
    }

    Java.perform(function() {
        send("Java runtime is now ready!");

        var ProtectedApp = Java.use("edts.klikidm.android.ProtectedApp");
        ProtectedApp.c.implementation = function() {
            send("ProtectedApp.c() executing original init...");
            var ret = this.c();
            send("ProtectedApp.c() finished! Harvesting 2903 strings in RAM...");

            try {
                var BufferedReader = Java.use("java.io.BufferedReader");
                var FileReader = Java.use("java.io.FileReader");
                var BufferedWriter = Java.use("java.io.BufferedWriter");
                var FileWriter = Java.use("java.io.FileWriter");

                var inPath = "/data/data/com.indomaret.klikindomaret/cache/all_enc_strings.txt";
                var outPath = "/data/data/com.indomaret.klikindomaret/cache/all_decrypted_strings.txt";

                var reader = BufferedReader.$new(FileReader.$new(inPath));
                var writer = BufferedWriter.$new(FileWriter.$new(outPath));

                var line = null;
                var count = 0;
                while ((line = reader.readLine()) !== null) {
                    var parts = line.split("|");
                    if (parts.length >= 2) {
                        var name = parts[0];
                        var enc = parts[1];
                        try {
                            var plain = ProtectedApp.s(enc);
                            writer.write(name + "=" + plain + "\\n");
                            count++;
                            if (count % 300 === 0) {
                                send("Harvested " + count + " strings...");
                            }
                        } catch(e) {
                            writer.write(name + "=[ERR: " + e + "]\\n");
                        }
                    }
                }
                reader.close();
                writer.flush();
                writer.close();
                send("SUCCESS_HARVESTED_" + count + "_STRINGS");
            } catch(err) {
                send("Harvester error: " + err);
            }

            return ret;
        };
    });
}

initHarvester();
"""

script = session.create_script(js_code)
script.on('message', on_message)
script.load()

print("[*] Resuming app to let DexProtector initialize...")
device.resume(pid)

for i in range(30):
    time.sleep(0.5)

session.detach()
