import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/**
 * Traduce los menus de Starsector reescribiendo literales dentro de los jar.
 *
 * No decide nada: el plan (plan.txt) dice exactamente que entrada del
 * constant pool de que clase hay que sustituir. Todo el analisis de que es
 * texto y que es un identificador se hizo al generar el plan.
 *
 * Siempre parte de una copia .orig intacta, asi que se puede repetir.
 */
public class Parchear {

    /** Sustituciones de una clase: indice de constant pool -> texto nuevo. */
    static class Clase {
        final Map<Integer, String> cambios = new HashMap<Integer, String>();
    }

    public static void main(String[] args) throws Exception {
        String juego = null;
        boolean restaurar = false;
        for (String a : args) {
            if (a == null || a.isEmpty()) continue;   // argumento vacio del .bat
            if (a.equals("--restaura")) restaurar = true;
            else juego = a;
        }
        if (juego == null) juego = System.getenv("STARSECTOR");
        if (juego == null) juego = ".";

        File raiz = new File(juego);
        if (!new File(raiz, "starfarer_obf.jar").isFile()) {
            System.err.println("No encuentro Starsector en: " + raiz.getAbsolutePath());
            System.err.println("Pasa la ruta como argumento.");
            System.exit(1);
        }

        if (restaurar) {
            restaurar(raiz);
            return;
        }

        File plan = new File(Parchear.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()).getParentFile();
        Map<String, Map<String, Clase>> porJar = leerPlan(new File(plan, "plan.txt"));

        int total = 0;
        for (Map.Entry<String, Map<String, Clase>> e : porJar.entrySet()) {
            total += parchearJar(new File(raiz, e.getKey()), e.getValue());
        }
        System.out.println();
        System.out.println(total + " literales traducidos.");
        System.out.println("Para volver atras:  java -jar parchear.jar \""
                + raiz.getAbsolutePath() + "\" --restaura");
    }

    // ---------------------------------------------------------------- plan

    static Map<String, Map<String, Clase>> leerPlan(File f) throws IOException {
        if (!f.isFile()) throw new FileNotFoundException("Falta plan.txt junto al jar");
        Map<String, Map<String, Clase>> porJar =
                new LinkedHashMap<String, Map<String, Clase>>();
        BufferedReader r = new BufferedReader(new InputStreamReader(
                new FileInputStream(f), StandardCharsets.UTF_8));
        try {
            String linea;
            Clase actual = null;
            while ((linea = r.readLine()) != null) {
                if (linea.isEmpty()) continue;
                String[] p = linea.split("\t", 3);
                if (p[0].equals("C")) {
                    Map<String, Clase> clases = porJar.get(p[1]);
                    if (clases == null) {
                        clases = new LinkedHashMap<String, Clase>();
                        porJar.put(p[1], clases);
                    }
                    actual = new Clase();
                    clases.put(p[2], actual);
                } else if (p[0].equals("S") && actual != null) {
                    actual.cambios.put(Integer.parseInt(p[1]), desescapar(p[2]));
                }
            }
        } finally {
            r.close();
        }
        return porJar;
    }

    static String desescapar(String s) {
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\' && i + 1 < s.length()) {
                char n = s.charAt(++i);
                if (n == 'n') sb.append('\n');
                else if (n == 't') sb.append('\t');
                else if (n == 'r') sb.append('\r');
                else sb.append(n);           // incluye la barra escapada
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    // ----------------------------------------------------------------- jar

    static File copia(File jar) throws IOException {
        File orig = new File(jar.getPath() + ".orig");
        if (!orig.isFile()) {
            Files.copy(jar.toPath(), orig.toPath(), StandardCopyOption.COPY_ATTRIBUTES);
        }
        return orig;
    }

    static int parchearJar(File jar, Map<String, Clase> clases) throws IOException {
        File orig = copia(jar);
        File tmp = new File(jar.getPath() + ".tmp");
        int cambios = 0;

        ZipFile ent = new ZipFile(orig);
        ZipOutputStream sal = new ZipOutputStream(new BufferedOutputStream(
                new FileOutputStream(tmp)));
        try {
            Enumeration<? extends ZipEntry> it = ent.entries();
            while (it.hasMoreElements()) {
                ZipEntry e = it.nextElement();
                byte[] datos = leer(ent.getInputStream(e), (int) Math.max(e.getSize(), 0));
                Clase c = clases.get(e.getName());
                if (c != null) {
                    byte[] nuevo = reescribir(datos, c.cambios);
                    if (nuevo != null) {
                        datos = nuevo;
                        cambios += c.cambios.size();
                    } else {
                        System.err.println("  aviso: " + e.getName() + " sin tocar");
                    }
                }
                ZipEntry salida = new ZipEntry(e.getName());
                salida.setTime(e.getTime());
                salida.setMethod(e.getMethod());
                if (e.getMethod() == ZipEntry.STORED) {
                    salida.setSize(datos.length);
                    salida.setCompressedSize(datos.length);
                    CRC32 crc = new CRC32();
                    crc.update(datos);
                    salida.setCrc(crc.getValue());
                }
                sal.putNextEntry(salida);
                sal.write(datos);
                sal.closeEntry();
            }
        } finally {
            sal.close();
            ent.close();
        }
        if (!jar.delete() || !tmp.renameTo(jar)) {
            throw new IOException("No se pudo reemplazar " + jar);
        }
        System.out.println("  " + jar.getName() + ": " + cambios + " literales");
        return cambios;
    }

    static byte[] leer(InputStream in, int pista) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream(Math.max(pista, 1024));
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        in.close();
        return out.toByteArray();
    }

    // ------------------------------------------------------- constant pool

    /** Bytes que ocupa cada entrada del pool, sin contar el tag. */
    static int tamano(byte[] d, int p, int tag) {
        switch (tag) {
            case 1:  return 2 + u2(d, p + 1);          // Utf8
            case 5: case 6: return 8;                  // Long, Double
            case 7: case 8: case 16: case 19: case 20: return 2;
            case 15: return 3;                         // MethodHandle
            case 3: case 4: case 9: case 10: case 11:
            case 12: case 17: case 18: return 4;
            default: return -1;
        }
    }

    static int u2(byte[] d, int p) {
        return ((d[p] & 0xff) << 8) | (d[p + 1] & 0xff);
    }

    /**
     * Sustituye las entradas Utf8 indicadas. Devuelve null si la clase no
     * parece un class file valido, para dejarla intacta en vez de romperla.
     */
    static byte[] reescribir(byte[] d, Map<Integer, String> cambios) {
        if (d.length < 10 || (d[0] & 0xff) != 0xca || (d[1] & 0xff) != 0xfe
                || (d[2] & 0xff) != 0xba || (d[3] & 0xff) != 0xbe) {
            return null;
        }
        int total = u2(d, 8);
        int p = 10, i = 1;
        // (inicio, fin) del texto de cada entrada que hay que cambiar
        List<int[]> tramos = new ArrayList<int[]>();
        List<String> textos = new ArrayList<String>();
        while (i < total) {
            if (p >= d.length) return null;
            int tag = d[p] & 0xff;
            int largo = tamano(d, p, tag);
            if (largo < 0) return null;
            if (tag == 1 && cambios.containsKey(i)) {
                int ini = p + 3, fin = p + 3 + u2(d, p + 1);
                tramos.add(new int[]{ini, fin});
                textos.add(cambios.get(i));
            }
            p += 1 + largo;
            i += (tag == 5 || tag == 6) ? 2 : 1;
        }
        if (tramos.size() != cambios.size()) return null;   // indices que no cuadran

        ByteArrayOutputStream out = new ByteArrayOutputStream(d.length + 4096);
        int cursor = 0;
        for (int k = 0; k < tramos.size(); k++) {
            int[] t = tramos.get(k);
            byte[] nuevo = textos.get(k).getBytes(StandardCharsets.UTF_8);
            out.write(d, cursor, t[0] - 2 - cursor);        // hasta la longitud
            out.write((nuevo.length >>> 8) & 0xff);
            out.write(nuevo.length & 0xff);
            out.write(nuevo, 0, nuevo.length);
            cursor = t[1];
        }
        out.write(d, cursor, d.length - cursor);
        byte[] res = out.toByteArray();
        // el resultado tiene que seguir siendo un class file recorrible
        return recorrible(res) ? res : null;
    }

    static boolean recorrible(byte[] d) {
        int total = u2(d, 8), p = 10, i = 1;
        while (i < total) {
            if (p >= d.length) return false;
            int tag = d[p] & 0xff;
            int largo = tamano(d, p, tag);
            if (largo < 0) return false;
            p += 1 + largo;
            i += (tag == 5 || tag == 6) ? 2 : 1;
        }
        return p <= d.length;
    }

    // ----------------------------------------------------------- restaurar

    static void restaurar(File raiz) throws IOException {
        String[] jars = {"starfarer_obf.jar", "starfarer.api.jar"};
        for (String j : jars) {
            File orig = new File(raiz, j + ".orig");
            if (orig.isFile()) {
                Files.copy(orig.toPath(), new File(raiz, j).toPath(),
                        StandardCopyOption.REPLACE_EXISTING);
                System.out.println("restaurado " + j);
            } else {
                System.out.println("sin copia de " + j);
            }
        }
    }
}
