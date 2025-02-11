import processing.core.PApplet;
import java.util.HashMap;
import java.util.Map;

public class Main extends PApplet {
	
	App app;
	
	public void settings() {
		size(1200, 600); // The size of the user window
		
	}
	
	public void setup() {
		app = new App(this); // Initialise the main application
	}
	
	public void draw() {
		app.update();
	}

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		PApplet.main("Main"); // Launch the Processing sketch
		
	}

}
