import frida, time, sys, os

device = frida.get_usb_device()
print("[*] Spawning com.indomaret.klikindomaret under Frida control...")
pid = device.spawn(["com.indomaret.klikindomaret"])
session = device.attach(pid)

js_code = """
Java.perform(function() {
    console.log("[*] Injected into process! Waiting for ProtectedApp.c()...");

    // 1. Hook ProtectedApp.c to decrypt immediately upon library initialization
    var ProtectedApp = Java.use("edts.klikidm.android.ProtectedApp");
    ProtectedApp.c.implementation = function() {
        console.log("[*] ProtectedApp.c() called! Executing original init...");
        var ret = this.c();
        console.log("[🔥] ProtectedApp.c() completed! DexProtector is ready. Starting string harvesting...");

        try {
            var File = Java.use("java.io.File");
            var BufferedReader = Java.use("java.io.BufferedReader");
            var FileReader = Java.use("java.io.FileReader");
            var BufferedWriter = Java.use("java.io.BufferedWriter");
            var FileWriter = Java.use("java.io.FileWriter");

            var reader = BufferedReader.$new(FileReader.$new("/data/local/tmp/all_enc_strings.txt"));
            var writer = BufferedWriter.$new(FileWriter.$new("/data/local/tmp/all_decrypted_strings.txt"));

            var line = null;
            var count = 0;
            while ((line = reader.readLine()) !== null) {
                var parts = line.split("|");
                if (parts.length >= 2) {
                    var name = parts[0];
                    var enc = parts[1];
                    try {
                        var dec = ProtectedApp.s(enc);
                        writer.write(name + "=" + dec + "\\n");
                        count++;
                    } catch(e) {
                        writer.write(name + "=[ERR: " + e + "]\\n");
                    }
                }
            }
            reader.close();
            writer.flush();
            writer.close();
            console.log("[✔✔✔] HARVESTED ALL " + count + " DECRYPTED STRINGS DIRECTLY IN RAM!");
        } catch(err) {
            console.log("[-] Harvester error: " + err);
        }

        return ret;
    };
});
"""

script = session.create_script(js_code)
script.load()

print("[*] Resuming app...")
device.resume(pid)

# Wait 8s for harvester to run
for _ in range(16):
    time.sleep(0.5)

session.detach()
