import processing.core.*;
import processing.awt.PSurfaceAWT;
import processing.data.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;

public class QuantumBrush extends PApplet {
    // Managers
    private CanvasManager canvas;
    private EffectManager effects;
    private StrokeManager strokes;
    private FileManager files;
    private UIManager ui;
    
    // UI components
    private JFrame controlFrame;
    private JFrame canvasFrame;
    private JMenuBar menuBar;
    private JComboBox<String> effectsDropdown;
    private JButton createButton;
    
    // Canvas state
    private PImage currentImage;
    private boolean isDrawing = false;
    private final float zoom = 1.0f;
    private String projectId = null;
    
    public static void main(String[] args) {
        PApplet.main("QuantumBrush");
    }
    
    public void settings() {
        size(800, 600);
    }
    
    public void setup() {
        // Initialize managers
        canvas = new CanvasManager(this);
        effects = new EffectManager(this);
        files = new FileManager(this);
        ui = new UIManager(this);
        strokes = new StrokeManager(this);
        
        // Load effects
        effects.loadEffects();
        
        // Setup UI
        setupUI();
        
        // Set default brush color
        stroke(255, 0, 0); // Red
        strokeWeight(2);
        
        // Add shutdown hook to clean up resources
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            if (strokes != null) {
                strokes.shutdown();
            }
        }));
        
        // Clean up any temporary files on startup
        cleanupTempFiles();
    }
    
    private void cleanupTempFiles() {
        try {
            // Clean up temp directory
            File tempDir = new File("temp");
            if (tempDir.exists() && tempDir.isDirectory()) {
                File[] tempFiles = tempDir.listFiles();
                if (tempFiles != null) {
                    for (File file : tempFiles) {
                        file.delete();
                    }
                }
            }
            
            // Clean up any lock files
            File[] lockFiles = new File(".").listFiles((dir, name) -> name.endsWith(".lock"));
            if (lockFiles != null) {
                for (File file : lockFiles) {
                    file.delete();
                }
            }
            
            // Clean up any temp files
            File[] tmpFiles = new File(".").listFiles((dir, name) -> name.endsWith(".tmp"));
            if (tmpFiles != null) {
                for (File file : tmpFiles) {
                    file.delete();
                }
            }
        } catch (Exception e) {
            System.err.println("Error cleaning up temporary files: " + e.getMessage());
        }
    }
    
    private void setupUI() {
        // Get the JFrame from Processing for canvas
        PSurfaceAWT.SmoothCanvas smoothCanvas = (PSurfaceAWT.SmoothCanvas) ((PSurfaceAWT)surface).getNative();
        canvasFrame = (JFrame) smoothCanvas.getFrame();
        canvasFrame.setTitle("Quantum Brush - Canvas");
        
        // Position the canvas frame on the right side of the screen
        Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
        canvasFrame.setLocation(screenSize.width/2, screenSize.height/4);
        
        // Create control frame
        createControlFrame();
        
        // Add keyboard shortcuts for undo/redo and zoom
        KeyboardFocusManager.getCurrentKeyboardFocusManager().addKeyEventDispatcher(new KeyEventDispatcher() {
            @Override
            public boolean dispatchKeyEvent(KeyEvent e) {
                if (e.getID() == KeyEvent.KEY_PRESSED) {
                    int keyCode = e.getKeyCode();
                    boolean isCtrlDown = (e.getModifiersEx() & InputEvent.CTRL_DOWN_MASK) != 0 ||
                                         (e.getModifiersEx() & InputEvent.META_DOWN_MASK) != 0;
                    boolean isShiftDown = (e.getModifiersEx() & InputEvent.SHIFT_DOWN_MASK) != 0;
                    
                    if (isCtrlDown) {
                        if (keyCode == KeyEvent.VK_Z) {
                            if (isShiftDown) {
                                // Redo (Ctrl/Cmd + Shift + Z)
                                canvas.redo();
                            } else {
                                // Undo (Ctrl/Cmd + Z)
                                canvas.undo();
                            }
                            return true;
                        }
                    }
                }
                return false;
            }
        });
        
        canvasFrame.setVisible(true);
    }
    
    private void createControlFrame() {
        // Create main control window
        controlFrame = new JFrame("Quantum Brush - Control Panel");
        controlFrame.setSize(600, 200);
        controlFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        // Position the control frame on the left side of the screen
        Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
        controlFrame.setLocation(screenSize.width/4, screenSize.height/4);
        
        // Create menu bar
        menuBar = new JMenuBar();
        
        // File menu
        JMenu fileMenu = new JMenu("File");
        JMenuItem newItem = new JMenuItem("New");
        JMenuItem openItem = new JMenuItem("Open");
        JMenuItem saveItem = new JMenuItem("Save");
        JMenuItem exitItem = new JMenuItem("Exit");
        
        // Add keyboard shortcuts
        newItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_N, 
            Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()));
        openItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_O, 
            Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()));
        saveItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_S, 
            Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()));
        
        newItem.addActionListener(e -> newFile());
        openItem.addActionListener(e -> openFile());
        saveItem.addActionListener(e -> saveFile());
        exitItem.addActionListener(e -> exit());
        
        fileMenu.add(newItem);
        fileMenu.add(openItem);
        fileMenu.add(saveItem);
        fileMenu.addSeparator();
        fileMenu.add(exitItem);
        
        // Edit menu
        JMenu editMenu = new JMenu("Edit");
        JMenuItem undoItem = new JMenuItem("Undo");
        JMenuItem redoItem = new JMenuItem("Redo");
        
        // Add keyboard shortcuts
        undoItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_Z, 
            Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()));
        redoItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_Z, 
            Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx() | InputEvent.SHIFT_DOWN_MASK));
        
        undoItem.addActionListener(e -> canvas.undo());
        redoItem.addActionListener(e -> canvas.redo());
        
        editMenu.add(undoItem);
        editMenu.add(redoItem);
        
        // Settings menu
        JMenu settingsMenu = new JMenu("Settings");
        JMenuItem pythonConfigItem = new JMenuItem("Configure Python");
        JMenuItem cleanupItem = new JMenuItem("Clean Up Temporary Files");
        
        pythonConfigItem.addActionListener(e -> strokes.showPythonConfigDialog());
        cleanupItem.addActionListener(e -> {
            cleanupTempFiles();
            JOptionPane.showMessageDialog(
                controlFrame,
                "Temporary files have been cleaned up.",
                "Cleanup Complete",
                JOptionPane.INFORMATION_MESSAGE
            );
        });
        
        settingsMenu.add(pythonConfigItem);
        settingsMenu.add(cleanupItem);
        
        // Help menu
        JMenu helpMenu = new JMenu("Help");
        JMenuItem aboutItem = new JMenuItem("About");
        JMenuItem viewLogItem = new JMenuItem("View Error Log");
        
        aboutItem.addActionListener(e -> showAbout());
        viewLogItem.addActionListener(e -> viewErrorLog());
        
        helpMenu.add(aboutItem);
        helpMenu.add(viewLogItem);
        
        // Add menus to menu bar
        menuBar.add(fileMenu);
        menuBar.add(editMenu);
        menuBar.add(settingsMenu);
        menuBar.add(helpMenu);
        
        // Set the menu bar
        controlFrame.setJMenuBar(menuBar);
        
        // Create main panel for controls
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Create control panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 5));
        
        // Add effects dropdown
        JLabel effectLabel = new JLabel("Quantum Effects:");
        effectsDropdown = new JComboBox<>();
        effectsDropdown.addItem("Select...");
        
        // Add effects from the effect manager
        for (String effectName : effects.getEffectNames()) {
            effectsDropdown.addItem(effectName);
        }
        
        effectsDropdown.setPreferredSize(new Dimension(200, 25));
        controlPanel.add(effectLabel);
        controlPanel.add(effectsDropdown);
        
        // Add Create button with custom styling
        createButton = new JButton("Create");
        createButton.setEnabled(false); // Initially disabled
        
        // Custom button styling
        createButton.setBackground(new Color(70, 130, 180)); // Steel blue
        createButton.setForeground(Color.WHITE);
        createButton.setFocusPainted(false);
        createButton.setBorderPainted(true);
        createButton.setContentAreaFilled(false);
        createButton.setOpaque(true);
        
        // Add a custom UI to maintain colors when pressed
        createButton.setUI(new javax.swing.plaf.basic.BasicButtonUI() {
            @Override
            public void update(Graphics g, JComponent c) {
                if (c.isOpaque()) {
                    if (c.isEnabled()) {
                        g.setColor(c.getBackground());
                    } else {
                        g.setColor(new Color(150, 150, 150)); // Gray for disabled
                    }
                    g.fillRect(0, 0, c.getWidth(), c.getHeight());
                }
                paint(g, c);
            }
        });
        
        // Add Stroke Manager button
        JButton strokeManagerButton = new JButton("Stroke Manager");
        strokeManagerButton.setBackground(new Color(46, 139, 87)); // Forest green
        strokeManagerButton.setForeground(Color.WHITE);
        strokeManagerButton.setFocusPainted(false);
        strokeManagerButton.setBorderPainted(true);
        strokeManagerButton.setContentAreaFilled(false);
        strokeManagerButton.setOpaque(true);
        
        // Add a custom UI to maintain colors when pressed
        strokeManagerButton.setUI(new javax.swing.plaf.basic.BasicButtonUI() {
            @Override
            public void update(Graphics g, JComponent c) {
                if (c.isOpaque()) {
                    if (c.isEnabled()) {
                        g.setColor(c.getBackground());
                    } else {
                        g.setColor(new Color(150, 150, 150)); // Gray for disabled
                    }
                    g.fillRect(0, 0, c.getWidth(), c.getHeight());
                }
                paint(g, c);
            }
        });
        
        strokeManagerButton.addActionListener(e -> {
            strokes.showStrokeManager();
        });

        // Add action listener to check if all conditions are met
        effectsDropdown.addActionListener(e -> {
            updateCreateButtonState();
        });
        
        createButton.addActionListener(e -> {
            String selectedEffect = (String) effectsDropdown.getSelectedItem();
            if (selectedEffect != null && !selectedEffect.equals("Select...")) {
                Effect effect = effects.getEffect(selectedEffect);
                if (effect != null) {
                    // Open effect configuration window
                    ui.createEffectWindow(effect);
                }
            } else {
                JOptionPane.showMessageDialog(controlFrame, 
                    "Please select an effect first.", 
                    "No Effect Selected", 
                    JOptionPane.WARNING_MESSAGE);
            }
        });
        
        controlPanel.add(createButton);
        controlPanel.add(strokeManagerButton);
        
        // Add to main panel
        mainPanel.add(controlPanel, BorderLayout.NORTH);
        
        // Add to frame
        controlFrame.add(mainPanel);
        controlFrame.setVisible(true);
    }
    
    // Method to update Create button state based on all conditions
    private void updateCreateButtonState() {
        boolean hasImage = (currentImage != null);
        boolean hasPath = canvas.hasPath();
        boolean hasEffect = effectsDropdown.getSelectedIndex() > 0; // Not "Select..."
        
        createButton.setEnabled(hasImage && hasPath && hasEffect);
    }
    
    public void draw() {
        background(240); // Lighter background for better contrast
        
        // Draw current image if exists
        if (currentImage != null) {
            image(currentImage, 0, 0);
        }
        
        // Draw current paths
        canvas.draw();
    }
    
    public void mousePressed() {
        if (currentImage != null) {
            isDrawing = true;
            canvas.startNewPath();
            canvas.setClickPoint(mouseX, mouseY);
            canvas.addPointToCurrentPath(mouseX, mouseY);
        }
    }
    
    public void mouseDragged() {
        if (isDrawing) {
            canvas.addPointToCurrentPath(mouseX, mouseY);
        }
    }
    
    public void mouseReleased() {
        if (isDrawing) {
            isDrawing = false;
            canvas.finishCurrentPath();
            
            // Update Create button state
            updateCreateButtonState();
        }
    }
    
    // File operations
    private void newFile() {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Select an image");
        fileChooser.setFileFilter(new javax.swing.filechooser.FileFilter() {
            public boolean accept(File f) {
                if (f.isDirectory()) return true;
                String name = f.getName().toLowerCase();
                return name.endsWith(".jpg") || name.endsWith(".jpeg") || 
                       name.endsWith(".png") || name.endsWith(".gif");
            }
            public String getDescription() {
                return "Image files (*.jpg, *.jpeg, *.png, *.gif)";
            }
        });
        
        if (fileChooser.showOpenDialog(controlFrame) == JFileChooser.APPROVE_OPTION) {
            File file = fileChooser.getSelectedFile();
            PImage loadedImage = loadImage(file.getAbsolutePath());
            
            // Prompt for project name
            String projectName = JOptionPane.showInputDialog(controlFrame, 
                "Enter a name for this project:", 
                "New Project", 
                JOptionPane.QUESTION_MESSAGE);
            
            if (projectName == null) {
                // User canceled
                return;
            }
            
            if (projectName.trim().isEmpty()) {
                projectName = "Untitled Project";
            }
            
            // Generate a new project ID
            projectId = "proj_" + System.currentTimeMillis();
            
            // Clear any existing strokes when creating a new project
            if (strokes != null) {
                strokes.clearStrokes();
            }
            
            // Rescale the image to fit the window if it's too large
            int maxWidth = 800;  // Maximum width for the canvas
            int maxHeight = 600; // Maximum height for the canvas
            
            if (loadedImage.width > maxWidth || loadedImage.height > maxHeight) {
                // Calculate scale factor to fit within max dimensions while preserving aspect ratio
                float widthRatio = (float)maxWidth / loadedImage.width;
                float heightRatio = (float)maxHeight / loadedImage.height;
                float scaleFactor = Math.min(widthRatio, heightRatio);
                
                // Resize the image
                int newWidth = (int)(loadedImage.width * scaleFactor);
                int newHeight = (int)(loadedImage.height * scaleFactor);
                
                loadedImage.resize(newWidth, newHeight);
                currentImage = loadedImage;
                
                // Resize window to match image size
                surface.setSize(newWidth, newHeight);
                System.out.println("Resized image to " + newWidth + "x" + newHeight);
            } else {
                currentImage = loadedImage;
                // Resize window to match image size
                surface.setSize(loadedImage.width, loadedImage.height);
            }
            
            // Create project directory and save original image
            files.saveProject(projectId, currentImage);
            
            // Create metadata
            files.createProjectMetadata(projectId, projectName);
            
            // Clear paths
            canvas.clearPaths();
            
            // Update Create button state
            updateCreateButtonState();
        }
    }
    
    private void openFile() {
        ArrayList<JSONObject> projects = files.getProjectsMetadata();
        
        if (projects.isEmpty()) {
            JOptionPane.showMessageDialog(controlFrame, 
                "No projects found. Create a new project first.", 
                "No Projects", 
                JOptionPane.INFORMATION_MESSAGE);
            return;
        }
        
        // Create a dialog for project selection
        JDialog dialog = new JDialog(controlFrame, "Open Project", true);
        dialog.setSize(500, 300);
        dialog.setLocationRelativeTo(controlFrame);
        
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));
        
        // Create project list panel
        JPanel listPanel = new JPanel(new BorderLayout());
        listPanel.setBorder(BorderFactory.createTitledBorder("Available Projects"));
        
        // Create project list model
        DefaultListModel<String> listModel = new DefaultListModel<>();
        JList<String> projectList = new JList<>(listModel);
        projectList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        // Map to store project IDs by display name
        Map<String, String> projectIdMap = new HashMap<>();
        
        // Populate list with project names
        for (JSONObject metadata : projects) {
            String projectName = metadata.getString("project_name", "Unnamed Project");
            String projectId = metadata.getString("project_id", "");
            long createdTime = metadata.getLong("created_time", 0);
            
            String displayName = projectName + " (" + files.formatTimestamp(createdTime) + ")";
            listModel.addElement(displayName);
            projectIdMap.put(displayName, projectId);
        }
        
        // Add list to scroll pane
        JScrollPane scrollPane = new JScrollPane(projectList);
        listPanel.add(scrollPane, BorderLayout.CENTER);
        
        // Create project details panel
        JPanel detailsPanel = new JPanel(new GridLayout(3, 1, 5, 5));
        detailsPanel.setBorder(BorderFactory.createTitledBorder("Project Details"));
        
        JLabel nameLabel = new JLabel("Name: ");
        JLabel createdLabel = new JLabel("Created: ");
        JLabel modifiedLabel = new JLabel("Modified: ");
        
        detailsPanel.add(nameLabel);
        detailsPanel.add(createdLabel);
        detailsPanel.add(modifiedLabel);
        
        // Add selection listener to update details
        projectList.addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                int selectedIndex = projectList.getSelectedIndex();
                if (selectedIndex >= 0) {
                    String displayName = listModel.getElementAt(selectedIndex);
                    String projectId = projectIdMap.get(displayName);
                    JSONObject metadata = files.getProjectMetadata(projectId);
                    
                    if (metadata != null) {
                        nameLabel.setText("Name: " + metadata.getString("project_name", "Unnamed Project"));
                        createdLabel.setText("Created: " + files.formatTimestamp(metadata.getLong("created_time", 0)));
                        modifiedLabel.setText("Modified: " + files.formatTimestamp(metadata.getLong("modified_time", 0)));
                    }
                }
            }
        });
        
        // Create button panel
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        
        JButton deleteButton = new JButton("Delete");
        deleteButton.setBackground(new Color(220, 53, 69)); // Bootstrap danger red
        deleteButton.setForeground(Color.WHITE);
        deleteButton.setFocusPainted(false);
        
        deleteButton.addActionListener(e -> {
            int selectedIndex = projectList.getSelectedIndex();
            if (selectedIndex >= 0) {
                String displayName = listModel.getElementAt(selectedIndex);
                String selectedProjectId = projectIdMap.get(displayName);
                
                if (selectedProjectId != null) {
                    // Confirm deletion
                    int confirm = JOptionPane.showConfirmDialog(
                        dialog,
                        "Are you sure you want to delete this project?\nThis action cannot be undone.",
                        "Confirm Deletion",
                        JOptionPane.YES_NO_OPTION,
                        JOptionPane.WARNING_MESSAGE
                    );
                    
                    if (confirm == JOptionPane.YES_OPTION) {
                        // Delete the project
                        boolean success = files.deleteProject(selectedProjectId);
                        
                        if (success) {
                            // Remove from list
                            listModel.remove(selectedIndex);
                            projectIdMap.remove(displayName);
                            
                            // Clear details
                            nameLabel.setText("Name: ");
                            createdLabel.setText("Created: ");
                            modifiedLabel.setText("Modified: ");
                            
                            // If current project was deleted, reset
                            if (selectedProjectId.equals(projectId)) {
                                projectId = null;
                                currentImage = null;
                                canvas.clearPaths();
                                strokes.clearStrokes();
                                updateCreateButtonState();
                                surface.setSize(800, 600);
                            }
                            
                            JOptionPane.showMessageDialog(
                                dialog,
                                "Project deleted successfully.",
                                "Project Deleted",
                                JOptionPane.INFORMATION_MESSAGE
                            );
                            
                            // If no more projects, close dialog
                            if (listModel.isEmpty()) {
                                dialog.dispose();
                                JOptionPane.showMessageDialog(
                                    controlFrame,
                                    "No more projects available. Create a new project.",
                                    "No Projects",
                                    JOptionPane.INFORMATION_MESSAGE
                                );
                            }
                        } else {
                            JOptionPane.showMessageDialog(
                                dialog,
                                "Failed to delete project. Please try again.",
                                "Delete Error",
                                JOptionPane.ERROR_MESSAGE
                            );
                        }
                    }
                }
            } else {
                JOptionPane.showMessageDialog(
                    dialog,
                    "Please select a project to delete.",
                    "No Selection",
                    JOptionPane.WARNING_MESSAGE
                );
            }
        });
        
        JButton cancelButton = new JButton("Cancel");
        cancelButton.addActionListener(e -> dialog.dispose());
        
        JButton openButton = new JButton("Open");
        openButton.addActionListener(e -> {
            int selectedIndex = projectList.getSelectedIndex();
            if (selectedIndex >= 0) {
                String displayName = listModel.getElementAt(selectedIndex);
                String selectedProjectId = projectIdMap.get(displayName);
                
                if (selectedProjectId != null) {
                    // Load the project
                    boolean success = files.loadProject(selectedProjectId);
                    
                    if (success) {
                        // Set the current project ID
                        projectId = selectedProjectId;
                        
                        // Clear any existing strokes when opening a project
                        if (strokes != null) {
                            strokes.clearStrokes();
                        }
                        
                        // Clear paths
                        canvas.clearPaths();
                        
                        // Update Create button state
                        updateCreateButtonState();
                        
                        dialog.dispose();
                    } else {
                        JOptionPane.showMessageDialog(dialog, 
                            "Failed to load project. The project may be corrupted.", 
                            "Load Error", 
                            JOptionPane.ERROR_MESSAGE);
                    }
                }
            } else {
                JOptionPane.showMessageDialog(dialog, 
                    "Please select a project to open.", 
                    "No Selection", 
                    JOptionPane.WARNING_MESSAGE);
            }
        });
        
        buttonPanel.add(deleteButton);
        buttonPanel.add(cancelButton);
        buttonPanel.add(openButton);
        
        // Add panels to main panel
        mainPanel.add(listPanel, BorderLayout.CENTER);
        mainPanel.add(detailsPanel, BorderLayout.SOUTH);
        mainPanel.add(buttonPanel, BorderLayout.SOUTH);
        
        // Add main panel to dialog
        dialog.add(mainPanel);
        dialog.setVisible(true);
    }
    
    private void updateProjectMetadata() {
        if (projectId != null) {
            files.updateProjectMetadata(projectId);
        }
    }
    
    private void saveFile() {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Save Image");
        fileChooser.setFileFilter(new javax.swing.filechooser.FileFilter() {
            public boolean accept(File f) {
                if (f.isDirectory()) return true;
                String name = f.getName().toLowerCase();
                return name.endsWith(".jpg") || name.endsWith(".jpeg") || 
                       name.endsWith(".png");
            }
            public String getDescription() {
                return "Image files (*.jpg, *.jpeg, *.png)";
            }
        });
        
        if (fileChooser.showSaveDialog(controlFrame) == JFileChooser.APPROVE_OPTION) {
            File selectedFile = fileChooser.getSelectedFile();
            // Make sure the file has an extension
            String path = selectedFile.getAbsolutePath();
            if (!path.toLowerCase().endsWith(".jpg") && 
                !path.toLowerCase().endsWith(".jpeg") && 
                !path.toLowerCase().endsWith(".png")) {
                path += ".png";
            }
            
            // Save the current canvas state
            PImage canvasImage = get();
            canvasImage.save(path);
            
            // Update metadata
            updateProjectMetadata();
            
            JOptionPane.showMessageDialog(controlFrame, "Image saved successfully!", "Save Complete", JOptionPane.INFORMATION_MESSAGE);
        }
    }
    
    private void showAbout() {
        JOptionPane.showMessageDialog(controlFrame, 
            "Quantum Brush\nA quantum computing visual effects application\nVersion 1.0", 
            "About Quantum Brush", 
            JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void viewErrorLog() {
        File logFile = new File("log/error.log");
        if (!logFile.exists()) {
            JOptionPane.showMessageDialog(
                controlFrame,
                "No error log found.",
                "No Log",
                JOptionPane.INFORMATION_MESSAGE
            );
            return;
        }
        
        try {
            // Read the log file
            StringBuilder logContent = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new FileReader(logFile))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    logContent.append(line).append("\n");
                }
            }
            
            // Create a dialog to display the log
            JDialog logDialog = new JDialog(controlFrame, "Error Log", true);
            logDialog.setSize(800, 600);
            logDialog.setLocationRelativeTo(controlFrame);
            
            JTextArea textArea = new JTextArea(logContent.toString());
            textArea.setEditable(false);
            textArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
            
            JScrollPane scrollPane = new JScrollPane(textArea);
            logDialog.add(scrollPane);
            
            // Add a button to clear the log
            JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
            JButton clearButton = new JButton("Clear Log");
            clearButton.addActionListener(e -> {
                try {
                    // Clear the log file
                    new FileWriter(logFile, false).close();
                    textArea.setText("");
                    JOptionPane.showMessageDialog(
                        logDialog,
                        "Log file cleared.",
                        "Log Cleared",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                } catch (IOException ex) {
                    JOptionPane.showMessageDialog(
                        logDialog,
                        "Failed to clear log file: " + ex.getMessage(),
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                    );
                }
            });
            buttonPanel.add(clearButton);
            
            JButton closeButton = new JButton("Close");
            closeButton.addActionListener(e -> logDialog.dispose());
            buttonPanel.add(closeButton);
            
            logDialog.add(buttonPanel, BorderLayout.SOUTH);
            
            logDialog.setVisible(true);
            
        } catch (IOException e) {
            JOptionPane.showMessageDialog(
                controlFrame,
                "Failed to read log file: " + e.getMessage(),
                "Error",
                JOptionPane.ERROR_MESSAGE
            );
        }
    }
    
    // Getters for managers
    public CanvasManager getCanvasManager() {
        return canvas;
    }
    
    public EffectManager getEffectManager() {
        return effects;
    }
    
    public StrokeManager getStrokeManager() {
        return strokes;
    }
    
    public FileManager getFileManager() {
        return files;
    }
    
    public UIManager getUIManager() {
        return ui;
    }
    
    public PImage getCurrentImage() {
        return currentImage;
    }
    
    public void setCurrentImage(PImage img) {
        this.currentImage = img;
    }
    
    public float getZoom() {
        return 1.0f;
    }
    
    public JButton getCreateButton() {
        return createButton;
    }
    
    public String getProjectId() {
        return projectId;
    }

    public PSurface getSurface() {
        return surface;
    }
    
    @Override
    public void exit() {
        // Clean up resources before exiting
        if (strokes != null) {
            strokes.shutdown();
        }
        super.exit();
    }
}
