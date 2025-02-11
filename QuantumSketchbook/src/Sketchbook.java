import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;

public class Sketchbook {
	private String filePath;
	private String name;
	private BufferedImage image;
	private Rectangle box;
	private int modifications;
	
	public Sketchbook(Property f, int x, int y, int width, int height) {
		// this.filePath = f.value;
		this.name = new File(filePath).getName().split("\\.")[0];
		this.box = new Rectangle(x, y, width, height);
		this.modifications = 0;
		// copyToTemp();
	}
}
