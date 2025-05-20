import processing.core.*;
import processing.data.*;
import java.util.*;
import java.io.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.nio.file.Paths;
import java.nio.file.Files;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class StrokeManager {
    private QuantumBrush app;
    private ArrayList<Stroke> strokes;
    private int currentStrokeIndex = -1;
    private String pythonCommand = null;
    private File pythonExecutable = null;
    
    // Thread pool for asynchronous processing
    private ExecutorService executorService;
    
    // Map to track which strokes are currently being processed
    private Map<String, Future<?>> processingStrokes;
    
    // Callback interface for UI updates
    public interface ProcessingCallback {
        void onProcessingComplete(String strokeId, boolean success);
    }
    
    private java.util.List<ProcessingCallback> callbacks;
    
    public StrokeManager(QuantumBrush app) {
        this.app = app;
        this.strokes = new ArrayList<>();
        this.executorService = Executors.newFixedThreadPool(3); // Allow up to 3 concurrent processes
        this.processingStrokes = new ConcurrentHashMap<>();
        this.callbacks = new ArrayList<>();
        
        // Initialize Python command on startup
        initializePythonCommand();
    }
    
    private void initializePythonCommand() {
        try {
            // First check if there's a saved custom Python path
            String customPath = loadCustomPythonPath();
            if (customPath != null && !customPath.isEmpty()) {
                File customPython = new File(customPath);
                if (customPython.exists() && customPython.canExecute()) {
                    pythonExecutable = customPython;
                    pythonCommand = customPython.getAbsolutePath();
                    System.out.println("Using custom Python path: " + pythonCommand);
                    return;
                } else {
                    System.err.println("Custom Python path is invalid: " + customPath);
                }
            }
            
            // If no custom path or it's invalid, try to find Python automatically
            boolean isWindows = System.getProperty("os.name").toLowerCase().contains("win");
            
            // Try python3 command first (for macOS/Linux)
            if (!isWindows) {
                if (findPythonExecutable("python3")) {
                    return;
                }
            }
            
            // Try python command (for Windows or as fallback)
            if (findPythonExecutable("python")) {
                return;
            }
            
            // Try specific python3.10+ commands as last resort
            String[] pythonCommands = {
                "python3.12", "python3.11", "python3.10", 
                "python312", "python311", "python310"
            };
            
            for (String cmd : pythonCommands) {
                if (findPythonExecutable(cmd)) {
                    return;
                }
            }
            
            // If we get here, we couldn't find a suitable Python version
            System.err.println(
                "WARNING: Could not find Python 3.10 or higher. " +
                "The application may not work correctly."
            );
            pythonCommand = isWindows ? "python" : "python3"; // Default fallback
            
        } catch (Exception e) {
            System.err.println("Error initializing Python command: " + e.getMessage());
            e.printStackTrace();
            pythonCommand = System.getProperty("os.name").toLowerCase().contains("win") ? 
                "python" : "python3";
        }
    }
    
    private boolean findPythonExecutable(String command) {
        try {
            // First try to find the full path of the executable
            ProcessBuilder whichBuilder;
            boolean isWindows = System.getProperty("os.name").toLowerCase().contains("win");
            
            if (isWindows) {
                whichBuilder = new ProcessBuilder("where", command);
            } else {
                whichBuilder = new ProcessBuilder("which", command);
            }
            
            whichBuilder.redirectErrorStream(true);
            Process whichProcess = whichBuilder.start();
            BufferedReader whichReader = new BufferedReader(
                new InputStreamReader(whichProcess.getInputStream())
            );
            String executablePath = whichReader.readLine(); // Get the first result
            whichProcess.waitFor();
            
            if (executablePath != null && !executablePath.isEmpty()) {
                File executable = new File(executablePath);
                if (executable.exists() && executable.canExecute()) {
                    System.out.println("Found Python executable: " + executablePath);
                    
                    // Now check the version
                    ProcessBuilder versionBuilder = new ProcessBuilder(executablePath, "--version");
                    versionBuilder.redirectErrorStream(true);
                    Process versionProcess = versionBuilder.start();
                    BufferedReader versionReader = new BufferedReader(
                        new InputStreamReader(versionProcess.getInputStream())
                    );
                    String versionLine = versionReader.readLine();
                    versionProcess.waitFor();
                    
                    if (versionLine != null && versionLine.toLowerCase().contains("python")) {
                        System.out.println("Python version: " + versionLine);
                        
                        // Extract version numbers
                        String[] parts = versionLine.split(" ")[1].split("\\.");
                        if (parts.length >= 2) {
                            int major = Integer.parseInt(parts[0]);
                            int minor = Integer.parseInt(parts[1]);
                            
                            boolean isCompatible = (major > 3) || 
                                                  (major == 3 && minor >= 10);
                            
                            if (isCompatible) {
                                System.out.println(
                                    "Using compatible Python: " + executablePath + 
                                    " (" + versionLine + ")"
                                );
                                pythonExecutable = executable;
                                pythonCommand = executablePath;
                                return true;
                            } else {
                                System.out.println(
                                    "Python version too old: " + versionLine + 
                                    " (need 3.10 or higher)"
                                );
                            }
                        }
                    }
                }
            }
            
            return false;
        } catch (Exception e) {
            System.out.println(
                "Error finding Python executable for " + command + ": " + e.getMessage()
            );
            return false;
        }
    }
    
    public void showPythonConfigDialog() {
        JDialog dialog = new JDialog((Frame)null, "Python Configuration", true);
        dialog.setSize(600, 300);
        dialog.setLocationRelativeTo(null);
        
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));
        
        // Current Python info
        JPanel infoPanel = new JPanel(new GridLayout(3, 1, 5, 5));
        infoPanel.setBorder(BorderFactory.createTitledBorder("Current Python Information"));
        
        String currentPath = pythonExecutable != null ? 
            pythonExecutable.getAbsolutePath() : pythonCommand;
        JLabel pathLabel = new JLabel("Path: " + currentPath);
        
        String versionInfo = "Unknown";
        try {
            ProcessBuilder pb = new ProcessBuilder(pythonCommand, "--version");
            pb.redirectErrorStream(true);
            Process process = pb.start();
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
            );
            versionInfo = reader.readLine();
            process.waitFor();
        } catch (Exception e) {
            versionInfo = "Error: " + e.getMessage();
        }
        
        JLabel versionLabel = new JLabel("Version: " + versionInfo);
        
        boolean isCompatible = versionInfo.matches(".*Python 3\\.1[0-9].*") || 
                              versionInfo.matches(".*Python 3\\.[2-9][0-9].*");
        String compatibilityMsg = isCompatible ? 
            "✓ Compatible with match-case syntax" : 
            "✗ Not compatible with match-case syntax (needs Python 3.10+)";
        JLabel compatLabel = new JLabel(compatibilityMsg);
        compatLabel.setForeground(isCompatible ? new Color(0, 150, 0) : Color.RED);
        
        infoPanel.add(pathLabel);
        infoPanel.add(versionLabel);
        infoPanel.add(compatLabel);
        
        // Custom path selection
        JPanel customPanel = new JPanel(new BorderLayout(5, 5));
        customPanel.setBorder(BorderFactory.createTitledBorder("Custom Python Path"));
        
        JTextField pathField = new JTextField(20);
        if (pythonExecutable != null) {
            pathField.setText(pythonExecutable.getAbsolutePath());
        }
        
        JButton browseButton = new JButton("Browse...");
        browseButton.addActionListener(e -> {
            JFileChooser fileChooser = new JFileChooser();
            fileChooser.setDialogTitle("Select Python Executable");
            
            // Set file filter based on OS
            boolean isWindows = System.getProperty("os.name").toLowerCase().contains("win");
            if (isWindows) {
                fileChooser.setFileFilter(new javax.swing.filechooser.FileFilter() {
                    public boolean accept(File f) {
                        return f.isDirectory() || f.getName().toLowerCase().endsWith(".exe");
                    }
                    public String getDescription() {
                        return "Executable files (*.exe)";
                    }
                });
            } else {
                fileChooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
            }
            
            if (fileChooser.showOpenDialog(dialog) == JFileChooser.APPROVE_OPTION) {
                File selectedFile = fileChooser.getSelectedFile();
                pathField.setText(selectedFile.getAbsolutePath());
            }
        });
        
        JPanel pathPanel = new JPanel(new BorderLayout(5, 0));
        pathPanel.add(pathField, BorderLayout.CENTER);
        pathPanel.add(browseButton, BorderLayout.EAST);
        
        JButton testButton = new JButton("Test Selected Python");
        testButton.addActionListener(e -> {
            String path = pathField.getText().trim();
            if (path.isEmpty()) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "Please enter a Python path first.", 
                    "No Path", 
                    JOptionPane.WARNING_MESSAGE
                );
                return;
            }
            
            File pythonFile = new File(path);
            if (!pythonFile.exists()) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "The specified file does not exist: " + path, 
                    "File Not Found", 
                    JOptionPane.ERROR_MESSAGE
                );
                return;
            }
            
            if (!pythonFile.canExecute()) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "The specified file is not executable: " + path, 
                    "Not Executable", 
                    JOptionPane.ERROR_MESSAGE
                );
                return;
            }
            
            try {
                ProcessBuilder pb = new ProcessBuilder(path, "--version");
                pb.redirectErrorStream(true);
                Process process = pb.start();
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream())
                );
                String version = reader.readLine();
                int exitCode = process.waitFor();
                
                if (exitCode == 0 && version != null && version.toLowerCase().contains("python")) {
                    boolean pythonCompatible = version.matches(".*Python 3\\.1[0-9].*") || 
                                              version.matches(".*Python 3\\.[2-9][0-9].*");
                    
                    if (pythonCompatible) {
                        JOptionPane.showMessageDialog(
                            dialog, 
                            "Python test successful!\n" + version + 
                            "\n\nThis version is compatible with match-case syntax.", 
                            "Test Successful", 
                            JOptionPane.INFORMATION_MESSAGE
                        );
                    } else {
                        JOptionPane.showMessageDialog(
                            dialog, 
                            "Python test successful, but version may be incompatible.\n" + 
                            version + 
                            "\n\nThis version may NOT support match-case syntax (needs Python 3.10+).", 
                            "Version Warning", 
                            JOptionPane.WARNING_MESSAGE
                        );
                    }
                } else {
                    JOptionPane.showMessageDialog(
                        dialog, 
                        "Failed to get Python version. Output: " + version, 
                        "Test Failed", 
                        JOptionPane.ERROR_MESSAGE
                    );
                }
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "Error testing Python: " + ex.getMessage(), 
                    "Test Error", 
                    JOptionPane.ERROR_MESSAGE
                );
            }
        });
        
        customPanel.add(pathPanel, BorderLayout.NORTH);
        customPanel.add(testButton, BorderLayout.SOUTH);
        
        // Button panel
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        
        JButton cancelButton = new JButton("Cancel");
        cancelButton.addActionListener(e -> dialog.dispose());
        
        JButton saveButton = new JButton("Save");
        saveButton.addActionListener(e -> {
            String path = pathField.getText().trim();
            if (path.isEmpty()) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "Please enter a Python path first.", 
                    "No Path", 
                    JOptionPane.WARNING_MESSAGE
                );
                return;
            }
            
            File pythonFile = new File(path);
            if (!pythonFile.exists() || !pythonFile.canExecute()) {
                JOptionPane.showMessageDialog(
                    dialog, 
                    "The specified file is not a valid executable: " + path, 
                    "Invalid Path", 
                    JOptionPane.ERROR_MESSAGE
                );
                return;
            }
            
            // Save the custom path
            saveCustomPythonPath(path);
            
            // Update the current Python command
            pythonExecutable = pythonFile;
            pythonCommand = path;
            
            JOptionPane.showMessageDialog(
                dialog, 
                "Python path saved successfully. It will be used for all future operations.", 
                "Path Saved", 
                JOptionPane.INFORMATION_MESSAGE
            );
            
            dialog.dispose();
        });
        
        buttonPanel.add(cancelButton);
        buttonPanel.add(saveButton);
        
        // Add all panels to main panel
        mainPanel.add(infoPanel, BorderLayout.NORTH);
        mainPanel.add(customPanel, BorderLayout.CENTER);
        mainPanel.add(buttonPanel, BorderLayout.SOUTH);
        
        dialog.add(mainPanel);
        dialog.setVisible(true);
    }
    
    private String loadCustomPythonPath() {
        try {
            File configFile = new File("config/python_path.txt");
            if (configFile.exists()) {
                return new String(Files.readAllBytes(configFile.toPath())).trim();
            }
        } catch (Exception e) {
            System.err.println("Error loading custom Python path: " + e.getMessage());
        }
        return null;
    }
    
    private void saveCustomPythonPath(String path) {
        try {
            File configDir = new File("config");
            if (!configDir.exists()) {
                configDir.mkdirs();
            }
            
            File configFile = new File("config/python_path.txt");
            Files.write(configFile.toPath(), path.getBytes());
            System.out.println("Saved custom Python path: " + path);
        } catch (Exception e) {
            System.err.println("Error saving custom Python path: " + e.getMessage());
        }
    }
    
    // Add a new method to check if any stroke is currently being processed
    public boolean isAnyStrokeProcessing() {
        // If the processing map is empty, no strokes are being processed
        if (processingStrokes.isEmpty()) {
            return false;
        }
        
        // Check if any of the futures in the map are not done
        for (Future<?> future : processingStrokes.values()) {
            if (!future.isDone()) {
                return true;
            }
        }
        
        // All futures are done, so no strokes are being processed
        return false;
    }
    
    // Modify the createStroke method to check for active processing
    public String createStroke(Effect effect, Map<String, Object> parameters) {
        // Check if any stroke is currently being processed
        if (isAnyStrokeProcessing()) {
            // Create a temporary file to store the current paths and parameters
            try {
                String tempId = "temp_" + System.currentTimeMillis();
                File tempDir = new File("temp");
                if (!tempDir.exists()) {
                    tempDir.mkdirs();
                }
                
                // Save the current state to a temporary file
                JSONObject tempState = new JSONObject();
                tempState.setString("effect_id", effect.getId());
                
                // Save parameters
                JSONObject paramsJson = new JSONObject();
                for (Map.Entry<String, Object> entry : parameters.entrySet()) {
                    if (entry.getValue() instanceof Integer) {
                        paramsJson.setInt(entry.getKey(), (Integer) entry.getValue());
                    } else if (entry.getValue() instanceof Float) {
                        paramsJson.setFloat(entry.getKey(), (Float) entry.getValue());
                    } else if (entry.getValue() instanceof Double) {
                        paramsJson.setFloat(entry.getKey(), ((Double) entry.getValue()).floatValue());
                    } else if (entry.getValue() instanceof Boolean) {
                        paramsJson.setBoolean(entry.getKey(), (Boolean) entry.getValue());
                    } else {
                        paramsJson.setString(entry.getKey(), entry.getValue().toString());
                    }
                }
                tempState.setJSONObject("parameters", paramsJson);
                
                // Save paths
                JSONArray pathsArray = new JSONArray();
                ArrayList<Path> currentPaths = app.getCanvasManager().getPaths();
                for (Path path : currentPaths) {
                    JSONObject pathJson = new JSONObject();
                    
                    // Save click point
                    PVector clickPoint = path.getClickPoint();
                    if (clickPoint != null) {
                        JSONArray clickArray = new JSONArray();
                        clickArray.append(clickPoint.x);
                        clickArray.append(clickPoint.y);
                        pathJson.setJSONArray("click_point", clickArray);
                    }
                    
                    // Save path points
                    JSONArray pointsArray = new JSONArray();
                    ArrayList<PVector> points = path.getPoints();
                    for (PVector point : points) {
                        JSONArray pointArray = new JSONArray();
                        pointArray.append(point.x);
                        pointArray.append(point.y);
                        pointsArray.append(pointArray);
                    }
                    pathJson.setJSONArray("points", pointsArray);
                    
                    pathsArray.append(pathJson);
                }
                tempState.setJSONArray("paths", pathsArray);
                
                // Save the temporary state
                app.saveJSONObject(tempState, "temp/" + tempId + ".json");
                
                // Show a message to the user
                SwingUtilities.invokeLater(() -> {
                    JOptionPane.showMessageDialog(
                        null,
                        "Another effect is currently being processed. Your stroke has been saved and will be processed once the current operation completes.",
                        "Processing in Progress",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                });
                
                // Return a special ID to indicate that the stroke was saved for later
                return "pending:" + tempId;
            } catch (Exception e) {
                System.err.println("Error saving temporary stroke: " + e.getMessage());
                e.printStackTrace();
                
                // Show an error message
                SwingUtilities.invokeLater(() -> {
                    JOptionPane.showMessageDialog(
                        null,
                        "Error saving your stroke: " + e.getMessage() + "\nPlease try again after the current processing completes.",
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                    );
                });
                
                return null;
            }
        }
        
        // If no stroke is being processed, continue with the normal flow
        // Generate stroke ID
        String strokeId = "stroke_" + System.currentTimeMillis();
        
        // Create stroke and add to list
        Stroke stroke = new Stroke(
            strokeId, 
            effect, 
            parameters, 
            app.getCanvasManager().getPaths()
        );
        strokes.add(stroke);
        
        // Get project ID
        String projectId = app.getProjectId();
        if (projectId == null) {
            System.err.println("Error: No project ID available");
            return null;
        }
        
        // Create project directory structure
        File projectDir = new File("project/" + projectId);
        if (!projectDir.exists()) {
            projectDir.mkdirs();
            
            // Save original image
            if (app.getCurrentImage() != null) {
                String originalPath = projectDir.getPath() + "/original.png";
                app.getCurrentImage().save(originalPath);
            }
        }
        
        // Create stroke directory
        File strokeDir = new File(projectDir, "stroke");
        if (!strokeDir.exists()) {
            strokeDir.mkdirs();
        }
        
        // Generate and save JSON instructions
        String instructionsPath = strokeDir.getPath() + "/" + strokeId + "_instructions.json";
        JSONObject instructions = stroke.generateJSON(projectId);
        app.saveJSONObject(instructions, instructionsPath);
        
        // Save input image
        if (app.getCurrentImage() != null) {
            String inputPath = strokeDir.getPath() + "/" + strokeId + "_input.png";
            app.getCurrentImage().save(inputPath);
            
            // Update JSON with image paths
            instructions = app.loadJSONObject(instructionsPath);
            JSONObject strokeInput = instructions.getJSONObject("stroke_input");
            strokeInput.setString("input_location", inputPath);
            strokeInput.setString(
                "output_location", 
                strokeDir.getPath() + "/" + strokeId + "_output.png"
            );
            instructions.setJSONObject("stroke_input", strokeInput);
            app.saveJSONObject(instructions, instructionsPath);
        }
        
        // Set current stroke index
        currentStrokeIndex = strokes.size() - 1;
        
        return strokeId;
    }
    
    // Add a new method to load existing strokes from the project folder
    public void loadExistingStrokes() {
        if (app.getProjectId() == null) {
            return;
        }
        
        String projectId = app.getProjectId();
        File strokeDir = new File("project/" + projectId + "/stroke");
        
        if (!strokeDir.exists() || !strokeDir.isDirectory()) {
            return;
        }
        
        // Get all instruction JSON files
        File[] instructionFiles = strokeDir.listFiles((dir, name) -> 
            name.endsWith("_instructions.json"));
        
        if (instructionFiles == null || instructionFiles.length == 0) {
            return;
        }
        
        // Clear existing strokes if we're reloading
        if (!strokes.isEmpty()) {
            strokes.clear();
        }
        
        // Process each instruction file
        for (File file : instructionFiles) {
            try {
                JSONObject instructions = app.loadJSONObject(file.getAbsolutePath());
                String strokeId = instructions.getString("stroke_id", "");
                String effectId = instructions.getString("effect_id", "");
                
                if (strokeId.isEmpty() || effectId.isEmpty()) {
                    continue;
                }
                
                // Get the effect
                Effect effect = app.getEffectManager().getEffect(effectId);
                if (effect == null) {
                    System.err.println("Effect not found: " + effectId);
                    continue;
                }
                
                // Extract parameters
                JSONObject userInput = instructions.getJSONObject("user_input");
                Map<String, Object> parameters = new HashMap<>();
                
                for (Object key : userInput.keys()) {
                    String paramName = (String) key;
                    Object value = userInput.get(paramName);
                    parameters.put(paramName, value);
                }
                
                // Extract path data
                JSONObject strokeInput = instructions.getJSONObject("stroke_input");
                JSONArray pathArray = strokeInput.getJSONArray("path");
                JSONArray clicksArray = strokeInput.getJSONArray("clicks");
                
                // Create a new path list
                ArrayList<Path> paths = new ArrayList<>();
                Path currentPath = new Path();
                
                // Add click points
                if (clicksArray != null && clicksArray.size() > 0) {
                    JSONArray clickPoint = clicksArray.getJSONArray(0);
                    if (clickPoint != null && clickPoint.size() >= 2) {
                        float x = clickPoint.getFloat(0);
                        float y = clickPoint.getFloat(1);
                        currentPath.setClickPoint(x, y);
                    }
                }
                
                // Add path points
                if (pathArray != null) {
                    for (int i = 0; i < pathArray.size(); i++) {
                        JSONArray point = pathArray.getJSONArray(i);
                        if (point != null && point.size() >= 2) {
                            float x = point.getFloat(0);
                            float y = point.getFloat(1);
                            currentPath.addPoint(x, y);
                        }
                    }
                }
                
                if (currentPath.hasPoints()) {
                    paths.add(currentPath);
                }
                
                // Create the stroke object and add it to the list
                Stroke stroke = new Stroke(strokeId, effect, parameters, paths);
                strokes.add(stroke);
                
            } catch (Exception e) {
                System.err.println("Error loading stroke from " + file.getName() + ": " + e.getMessage());
                e.printStackTrace();
            }
        }
        
        // After loading all strokes, sort them by timestamp (most recent last)
        if (!strokes.isEmpty()) {
            strokes.sort((a, b) -> {
              // Extract timestamp from stroke ID (format: stroke_timestamp)
              long timeA = Long.parseLong(a.getId().substring(a.getId().indexOf('_') + 1));
              long timeB = Long.parseLong(b.getId().substring(b.getId().indexOf('_') + 1));
              return Long.compare(timeA, timeB);
            });
            
            // Set current stroke index to the most recent stroke
            currentStrokeIndex = strokes.size() - 1;
        }
    }

    // Modify the showStrokeManager method to load existing strokes
    public void showStrokeManager() {
        // Load existing strokes first
        loadExistingStrokes();
        
        if (!strokes.isEmpty()) {
            app.getUIManager().createStrokeManagerWindow(this);
        } else {
            // Instead of showing a message that blocks interaction, show a non-modal dialog
            JOptionPane optionPane = new JOptionPane(
                "No strokes available. Create a stroke first by drawing a path and clicking 'Create'.",
                JOptionPane.INFORMATION_MESSAGE
            );
            JDialog dialog = optionPane.createDialog("No Strokes");
            dialog.setModal(false);
            dialog.setVisible(true);
            
            // Auto-close the dialog after 3 seconds
            javax.swing.Timer timer = new javax.swing.Timer(3000, e -> dialog.dispose());
            timer.setRepeats(false);
            timer.start();
        }
    }
    
    public Stroke getCurrentStroke() {
        if (currentStrokeIndex >= 0 && currentStrokeIndex < strokes.size()) {
            return strokes.get(currentStrokeIndex);
        }
        return null;
    }
    
    public void nextStroke() {
        if (currentStrokeIndex < strokes.size() - 1) {
            currentStrokeIndex++;
        }
    }
    
    public void previousStroke() {
        if (currentStrokeIndex > 0) {
            currentStrokeIndex--;
        }
    }
    
    public void runCurrentStroke() {
        Stroke stroke = getCurrentStroke();
        if (stroke != null) {
            runStroke(stroke);
        } else {
            JOptionPane.showMessageDialog(
                null, 
                "No stroke selected or available.", 
                "No Stroke", 
                JOptionPane.WARNING_MESSAGE
            );
        }
    }
    
    // Add a method to process pending strokes
    public void processPendingStrokes() {
        File tempDir = new File("temp");
        if (!tempDir.exists() || !tempDir.isDirectory()) {
            return;
        }
        
        // Get all temporary stroke files
        File[] tempFiles = tempDir.listFiles((dir, name) -> name.endsWith(".json"));
        if (tempFiles == null || tempFiles.length == 0) {
            return;
        }
        
        // Process each temporary stroke
        for (File tempFile : tempFiles) {
            try {
                // Load the temporary state
                JSONObject tempState = app.loadJSONObject(tempFile.getAbsolutePath());
                
                // Get the effect
                String effectId = tempState.getString("effect_id", "");
                if (effectId.isEmpty()) {
                    System.err.println("Error: No effect ID in temporary stroke file");
                    tempFile.delete();
                    continue;
                }
                
                Effect effect = app.getEffectManager().getEffect(effectId);
                if (effect == null) {
                    System.err.println("Error: Effect not found: " + effectId);
                    tempFile.delete();
                    continue;
                }
                
                // Get the parameters
                JSONObject paramsJson = tempState.getJSONObject("parameters");
                Map<String, Object> parameters = new HashMap<>();
                for (Object key : paramsJson.keys()) {
                    String paramName = (String) key;
                    parameters.put(paramName, paramsJson.get(paramName));
                }
                
                // Get the paths
                JSONArray pathsArray = tempState.getJSONArray("paths");
                ArrayList<Path> paths = new ArrayList<>();
                for (int i = 0; i < pathsArray.size(); i++) {
                    JSONObject pathJson = pathsArray.getJSONObject(i);
                    Path path = new Path();
                    
                    // Get click point
                    if (pathJson.hasKey("click_point")) {
                        JSONArray clickArray = pathJson.getJSONArray("click_point");
                        if (clickArray != null && clickArray.size() >= 2) {
                            float x = clickArray.getFloat(0);
                            float y = clickArray.getFloat(1);
                            path.setClickPoint(x, y);
                        }
                    }
                    
                    // Get path points
                    JSONArray pointsArray = pathJson.getJSONArray("points");
                    if (pointsArray != null) {
                        for (int j = 0; j < pointsArray.size(); j++) {
                            JSONArray pointArray = pointsArray.getJSONArray(j);
                            if (pointArray != null && pointArray.size() >= 2) {
                                float x = pointArray.getFloat(0);
                                float y = pointArray.getFloat(1);
                                path.addPoint(x, y);
                            }
                        }
                    }
                    
                    if (path.hasPoints()) {
                        paths.add(path);
                    }
                }
                
                // Create the stroke
                String strokeId = "stroke_" + System.currentTimeMillis();
                Stroke stroke = new Stroke(strokeId, effect, parameters, paths);
                strokes.add(stroke);
                
                // Get project ID
                String projectId = app.getProjectId();
                if (projectId == null) {
                    System.err.println("Error: No project ID available");
                    tempFile.delete();
                    continue;
                }
                
                // Create project directory structure
                File projectDir = new File("project/" + projectId);
                if (!projectDir.exists()) {
                    projectDir.mkdirs();
                    
                    // Save original image
                    if (app.getCurrentImage() != null) {
                        String originalPath = projectDir.getPath() + "/original.png";
                        app.getCurrentImage().save(originalPath);
                    }
                }
                
                // Create stroke directory
                File strokeDir = new File(projectDir, "stroke");
                if (!strokeDir.exists()) {
                    strokeDir.mkdirs();
                }
                
                // Generate and save JSON instructions
                String instructionsPath = strokeDir.getPath() + "/" + strokeId + "_instructions.json";
                JSONObject instructions = stroke.generateJSON(projectId);
                app.saveJSONObject(instructions, instructionsPath);
                
                // Save input image
                if (app.getCurrentImage() != null) {
                    String inputPath = strokeDir.getPath() + "/" + strokeId + "_input.png";
                    app.getCurrentImage().save(inputPath);
                    
                    // Update JSON with image paths
                    instructions = app.loadJSONObject(instructionsPath);
                    JSONObject strokeInput = instructions.getJSONObject("stroke_input");
                    strokeInput.setString("input_location", inputPath);
                    strokeInput.setString(
                        "output_location", 
                        strokeDir.getPath() + "/" + strokeId + "_output.png"
                    );
                    instructions.setJSONObject("stroke_input", strokeInput);
                    app.saveJSONObject(instructions, instructionsPath);
                }
                
                // Set current stroke index
                currentStrokeIndex = strokes.size() - 1;
                
                // Delete the temporary file
                tempFile.delete();
                
                // Show a message to the user
                SwingUtilities.invokeLater(() -> {
                    JOptionPane.showMessageDialog(
                        null,
                        "Your saved stroke has been processed and is now available in the Stroke Manager.",
                        "Stroke Processed",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                    
                    // Open the Stroke Manager
                    app.getUIManager().createStrokeManagerWindow(this);
                });
                
            } catch (Exception e) {
                System.err.println("Error processing temporary stroke: " + e.getMessage());
                e.printStackTrace();
                tempFile.delete();
            }
        }
    }
    
    /**
     * Runs the effect processing for a stroke asynchronously.
     * This method will not block the UI thread.
     */
    public void runStroke(Stroke stroke) {
        try {
            final String strokeId = stroke.getId();
            
            // Check if this stroke is already being processed
            if (processingStrokes.containsKey(strokeId)) {
                JOptionPane.showMessageDialog(
                    null, 
                    "This stroke is already being processed. Please wait for it to complete.", 
                    "Processing in Progress", 
                    JOptionPane.INFORMATION_MESSAGE
                );
                return;
            }
            
            Effect effect = stroke.getEffect();
            String effectId = effect.getId();
            String folderName = effect.getFolderName();
            final String projectId = app.getProjectId();
            
            // Define instructionsPath once here to use throughout the method
            final String instructionsPath = "project/" + projectId + "/stroke/" + strokeId + "_instructions.json";
            File instructionsFile = new File(instructionsPath);
            
            // Check if the stroke is in a failed state and needs cleanup
            if (instructionsFile.exists()) {
                JSONObject instructions = app.loadJSONObject(instructionsPath);
                String processingStatus = instructions.getString("processing_status", "");
                
                // If the stroke is in a "running" state but not in our processing map,
                // it means the previous run crashed or was interrupted
                if ("running".equals(processingStatus) && !processingStrokes.containsKey(strokeId)) {
                    // Reset the status to allow reprocessing
                    instructions.setString("processing_status", "pending");
                    app.saveJSONObject(instructions, instructionsPath);
                }
            }
            
            // Check if Python script exists
            File pythonScript = new File("effect/" + folderName + "/" + effectId + ".py");
            if (!pythonScript.exists()) {
                // Try with folder name as fallback
                pythonScript = new File("effect/" + folderName + "/" + folderName + ".py");
                if (!pythonScript.exists()) {
                    JOptionPane.showMessageDialog(
                        null, 
                        "Python script not found: " + pythonScript.getAbsolutePath(), 
                        "Error", 
                        JOptionPane.ERROR_MESSAGE
                    );
                    return;
                }
            }
            
            // Ensure directories exist
            File projectDir = new File("project/" + projectId);
            File strokeDir = new File(projectDir, "stroke");
            if (!projectDir.exists()) projectDir.mkdirs();
            if (!strokeDir.exists()) strokeDir.mkdirs();
            
            // Ensure instructions file exists
            if (!instructionsFile.exists()) {
                JSONObject instructions = stroke.generateJSON(projectId);
                app.saveJSONObject(instructions, instructionsPath);
            }
            
            // Update status fields to indicate processing has started
            JSONObject instructions = app.loadJSONObject(instructionsPath);
            instructions.setBoolean("created", true);
            instructions.setString("effect_received", "null");
            instructions.setString("effect_processed", "null");
            instructions.setString("effect_success", "null");
            instructions.setString("processing_status", "running");
            app.saveJSONObject(instructions, instructionsPath);
            
            // Create a task to execute the Python script asynchronously
            Runnable task = () -> {
                boolean success = false;
                Process pythonProcess = null;
                
                try {
                    // Execute Python script with absolute path
                    success = executeApplyEffectScript(instructionsFile.getAbsolutePath(), pythonProcess);
                    
                    // Update status based on result
                    JSONObject updatedInstructions = app.loadJSONObject(instructionsPath);
                    if (success) {
                        updatedInstructions.setString("effect_received", "true");
                        updatedInstructions.setString("effect_processed", "true");
                        updatedInstructions.setString("effect_success", "true");
                        updatedInstructions.setString("processing_status", "completed");
                        app.saveJSONObject(updatedInstructions, instructionsPath);
                        
                        // Create layered image
                        String layeredPath = createLayeredImage(projectId, strokeId);
                        
                        // Update the instructions with the layered image path
                        updatedInstructions = app.loadJSONObject(instructionsPath);
                        updatedInstructions.setString("layered_output_location", layeredPath);
                        app.saveJSONObject(updatedInstructions, instructionsPath);
                        
                        // Notify on the Event Dispatch Thread
                        SwingUtilities.invokeLater(() -> {
                            notifyProcessingComplete(strokeId, true);
                        });
                    } else {
                        updatedInstructions.setString("effect_received", "true");
                        updatedInstructions.setString("effect_processed", "true");
                        updatedInstructions.setString("effect_success", "false");
                        updatedInstructions.setString("processing_status", "failed");
                        app.saveJSONObject(updatedInstructions, instructionsPath);
                        
                        // Notify on the Event Dispatch Thread
                        SwingUtilities.invokeLater(() -> {
                            notifyProcessingComplete(strokeId, false);
                        });
                    }
                } catch (InterruptedException e) {
                    // This exception is thrown when the thread is interrupted (e.g., when cancelling)
                    System.err.println("Python process execution interrupted");
                    
                    // Make sure to kill the Python process if it's still running
                    if (pythonProcess != null && pythonProcess.isAlive()) {
                        pythonProcess.destroyForcibly();
                        System.out.println("Forcibly terminated Python process due to cancellation");
                    }
                    
                    // Update the instructions file to reflect cancellation
                    try {
                        JSONObject updatedInstructions = app.loadJSONObject(instructionsPath);
                        updatedInstructions.setString("effect_success", "false");
                        updatedInstructions.setString("processing_status", "canceled");
                        updatedInstructions.setString("error_message", "Process was cancelled by user");
                        app.saveJSONObject(updatedInstructions, instructionsPath);
                    } catch (Exception ex) {
                        System.err.println("Error updating instructions file after cancellation: " + ex.getMessage());
                    }
                    
                    // Notify on the Event Dispatch Thread
                    SwingUtilities.invokeLater(() -> {
                        notifyProcessingComplete(strokeId, false);
                    });
                    
                    // Preserve interrupt status
                    Thread.currentThread().interrupt();
                } catch (Exception e) {
                    System.err.println("Error in background processing: " + e.getMessage());
                    e.printStackTrace();
                    
                    try {
                        JSONObject updatedInstructions = app.loadJSONObject(instructionsPath);
                        updatedInstructions.setString("effect_success", "false");
                        updatedInstructions.setString("processing_status", "failed");
                        updatedInstructions.setString("error_message", e.getMessage());
                        app.saveJSONObject(updatedInstructions, instructionsPath);
                    } catch (Exception ex) {
                        System.err.println("Error updating instructions file: " + ex.getMessage());
                    }
                    
                    // Notify on the Event Dispatch Thread
                    SwingUtilities.invokeLater(() -> {
                        notifyProcessingComplete(strokeId, false);
                    });
                }
            };
            
            // Submit the task to the executor service
            Future<?> future = executorService.submit(task);
            
            // Store the future for potential cancellation
            processingStrokes.put(strokeId, future);
            
            // Notify the UI that processing has started
            SwingUtilities.invokeLater(() -> {
                app.getUIManager().updateStrokeManagerContent(this);
                
                // Show a non-blocking notification
                JOptionPane optionPane = new JOptionPane(
                    "Effect processing started in the background.\n" +
                    "You can continue using the application while it processes.",
                    JOptionPane.INFORMATION_MESSAGE
                );
                JDialog dialog = optionPane.createDialog("Processing Started");
                dialog.setModal(false);
                dialog.setVisible(true);
                
                // Auto-close the dialog after 3 seconds
                javax.swing.Timer timer = new javax.swing.Timer(3000, e -> dialog.dispose());
                timer.setRepeats(false);
                timer.start();
            });
            
        } catch (Exception e) {
            System.err.println("Error starting effect processing: " + e.getMessage());
            e.printStackTrace();
            JOptionPane.showMessageDialog(
                null, 
                "Error starting effect processing: " + e.getMessage(), 
                "Error", 
                JOptionPane.ERROR_MESSAGE
            );
        }
    }
    
    /**
     * Cancels the processing of a stroke if it's currently running.
     * 
     * @param strokeId The ID of the stroke to cancel
     * @return true if the stroke was canceled, false if it wasn't running or couldn't be canceled
     */
    public boolean cancelStrokeProcessing(String strokeId) {
        Future<?> future = processingStrokes.get(strokeId);
        if (future != null && !future.isDone()) {
            // Cancel the future with interruption
            boolean canceled = future.cancel(true);
        
            if (canceled) {
                // Remove from processing map immediately to prevent race conditions
                processingStrokes.remove(strokeId);
            
                // Update the status in the instructions file
                try {
                    String projectId = app.getProjectId();
                    String instructionsPath = "project/" + projectId + "/stroke/" + strokeId + "_instructions.json";
                    JSONObject instructions = app.loadJSONObject(instructionsPath);
                    instructions.setString("processing_status", "canceled");
                    instructions.setString("effect_success", "false");
                    instructions.setString("error_message", "Process was cancelled by user");
                    app.saveJSONObject(instructions, instructionsPath);
                } catch (Exception e) {
                    System.err.println("Error updating instructions file: " + e.getMessage());
                }
            
                // Notify the UI
                SwingUtilities.invokeLater(() -> {
                    app.getUIManager().updateStrokeManagerContent(this);
                
                    // Show a non-blocking notification
                    JOptionPane optionPane = new JOptionPane(
                        "Effect processing has been cancelled.",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                    JDialog dialog = optionPane.createDialog("Processing Cancelled");
                    dialog.setModal(false);
                    dialog.setVisible(true);
                
                    // Auto-close the dialog after 2 seconds
                    javax.swing.Timer timer = new javax.swing.Timer(2000, e -> dialog.dispose());
                    timer.setRepeats(false);
                    timer.start();
                });
            }
            return canceled;
        }
        return false;
    }
    
    /**
     * Adds a callback to be notified when stroke processing completes.
     */
    public void addProcessingCallback(ProcessingCallback callback) {
        if (!callbacks.contains(callback)) {
            callbacks.add(callback);
        }
    }
    
    /**
     * Removes a processing callback.
     */
    public void removeProcessingCallback(ProcessingCallback callback) {
        callbacks.remove(callback);
    }
    
    /**
     * Notifies all registered callbacks that processing has completed.
     */
    private void notifyProcessingComplete(String strokeId, boolean success) {
        // Remove from processing map before notifying callbacks
        processingStrokes.remove(strokeId);
        
        // Show a notification regardless of whether the stroke manager is open
        SwingUtilities.invokeLater(() -> {
          String message = success ? 
            "Effect processed successfully!" : 
            "Effect processing failed. Check the error log for details.";
          
          JOptionPane optionPane = new JOptionPane(
            message,
            success ? JOptionPane.INFORMATION_MESSAGE : JOptionPane.ERROR_MESSAGE
          );
          JDialog dialog = optionPane.createDialog("Processing Complete");
          dialog.setModal(false);
          dialog.setVisible(true);
          
          // Auto-close the dialog after 3 seconds
          javax.swing.Timer timer = new javax.swing.Timer(3000, evt -> dialog.dispose());
          timer.setRepeats(false);
          timer.start();
        });
        
        // Now notify all registered callbacks
        for (ProcessingCallback callback : callbacks) {
            callback.onProcessingComplete(strokeId, success);
        }
        
        // Check if there are any pending strokes to process
        if (processingStrokes.isEmpty()) {
            processPendingStrokes();
        }
    }
    
    /**
     * Checks if a stroke is currently being processed.
     */
    public boolean isStrokeProcessing(String strokeId) {
        Future<?> future = processingStrokes.get(strokeId);
        return future != null && !future.isDone();
    }
    
    /**
     * Gets the processing status of a stroke from its instructions file.
     */
    public String getStrokeProcessingStatus(String strokeId) {
        try {
            String projectId = app.getProjectId();
            String instructionsPath = "project/" + projectId + "/stroke/" + strokeId + "_instructions.json";
            File instructionsFile = new File(instructionsPath);
            
            if (instructionsFile.exists()) {
                JSONObject instructions = app.loadJSONObject(instructionsPath);
                return instructions.getString("processing_status", "unknown");
            }
        } catch (Exception e) {
            System.err.println("Error getting stroke status: " + e.getMessage());
        }
        return "unknown";
    }
    
    private boolean executeApplyEffectScript(String instructionsFilePath, Process processRef) throws InterruptedException, IOException {
        Process process = null;
        try {
            // Check if we need to re-initialize Python command
            if (pythonCommand == null) {
                initializePythonCommand();
            }
            
            // Create log directory if it doesn't exist
            File logDir = new File("log");
            if (!logDir.exists()) {
                logDir.mkdirs();
            }
            
            // Create log files for stdout and stderr
            File stdoutLog = new File("log/python_stdout.log");
            File stderrLog = new File("log/python_stderr.log");
            
            // Display Python version information
            ProcessBuilder versionProcessBuilder = new ProcessBuilder(pythonCommand, "--version");
            versionProcessBuilder.redirectErrorStream(true);
            
            Process versionProcess = versionProcessBuilder.start();
            BufferedReader versionReader = new BufferedReader(
                new InputStreamReader(versionProcess.getInputStream())
            );
            String versionLine;
            while ((versionLine = versionReader.readLine()) != null) {
                System.out.println(
                    "Using Python: " + versionLine + " (from: " + pythonCommand + ")"
                );
                
                // Check if version is compatible with match-case syntax (Python 3.10+)
                if (versionLine.matches(".*Python 3\\.[0-9](\\..*)?")) {
                    String minorVersionStr = versionLine.replaceAll(
                        ".*Python 3\\.([0-9])(\\..*)?", "$1"
                    );
                    try {
                        int minorVersion = Integer.parseInt(minorVersionStr);
                        if (minorVersion < 10) {
                            System.err.println(
                                "WARNING: Python version is " + versionLine + 
                                " but match-case syntax requires Python 3.10 or higher!"
                            );
                            
                            // Don't show dialog in background thread
                            return false;
                        }
                    } catch (NumberFormatException e) {
                        System.err.println("Could not parse Python version: " + versionLine);
                    }
                }
            }
            versionProcess.waitFor();
            
            // Create command to execute Python script with better error handling
            ProcessBuilder processBuilder = new ProcessBuilder(
                pythonCommand, "effect/apply_effect.py", instructionsFilePath
            );
            processBuilder.redirectOutput(ProcessBuilder.Redirect.appendTo(stdoutLog));
            processBuilder.redirectError(ProcessBuilder.Redirect.appendTo(stderrLog));
            
            // Execute process
            process = processBuilder.start();
            
            // Store the process reference for potential cancellation
            if (processRef != null) {
                processRef = process;
            }
            
            // Add a timeout to prevent hanging
            boolean completed = process.waitFor(60, java.util.concurrent.TimeUnit.SECONDS);
            
            if (!completed) {
                process.destroyForcibly();
                System.err.println("Python script execution timed out after 60 seconds");
                
                // Update the instructions file
                JSONObject instructions = app.loadJSONObject(instructionsFilePath);
                instructions.setString("effect_success", "false");
                instructions.setString("error_message", "Execution timed out after 60 seconds");
                app.saveJSONObject(instructions, instructionsFilePath);
                
                return false;
            }
            
            // Get exit code
            int exitCode = process.exitValue();
            
            // Check the effect_success flag in the JSON file
            JSONObject instructions = app.loadJSONObject(instructionsFilePath);
            String effectSuccess = instructions.getString("effect_success", "false");
            
            // Check if output file exists
            String projectId = instructions.getString("project_id", "");
            String strokeId = instructions.getString("stroke_id", "");
            String outputPath = "project/" + projectId + "/stroke/" + strokeId + "_output.png";
            File outputFile = new File(outputPath);
            
            boolean success = exitCode == 0 && "true".equals(effectSuccess) && outputFile.exists();
            
            if (!success) {
                System.err.println("Python script execution failed with exit code: " + exitCode);
                System.err.println("Effect success flag: " + effectSuccess);
                System.err.println("Output file exists: " + outputFile.exists());
                
                // Read error log
                if (stderrLog.exists()) {
                    try (BufferedReader reader = new BufferedReader(new FileReader(stderrLog))) {
                        String line;
                        System.err.println("Python error log:");
                        while ((line = reader.readLine()) != null) {
                            System.err.println("  " + line);
                        }
                    } catch (IOException e) {
                        System.err.println("Could not read error log: " + e.getMessage());
                    }
                }
            }
            
            return success;
            
        } catch (InterruptedException e) {
            // This exception is thrown when the thread is interrupted (e.g., when cancelling)
            System.err.println("Python process execution interrupted");
            
            // Make sure to kill the Python process if it's still running
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
                System.out.println("Forcibly terminated Python process due to cancellation");
            }
            
            // Update the instructions file to reflect cancellation
            try {
                JSONObject instructions = app.loadJSONObject(instructionsFilePath);
                instructions.setString("effect_success", "false");
                instructions.setString("processing_status", "canceled");
                instructions.setString("error_message", "Process was cancelled by user");
                app.saveJSONObject(instructions, instructionsFilePath);
            } catch (Exception ex) {
                System.err.println("Error updating instructions file after cancellation: " + ex.getMessage());
            }
            
            // Re-throw the exception to be handled by the caller
            throw e;
        }
    }
    
    public String createLayeredImage(String projectId, String strokeId) {
        try {
            // Get paths for input and output images
            String inputPath = "project/" + projectId + "/original.png";
            String outputPath = "project/" + projectId + "/stroke/" + strokeId + "_output.png";
            
            // Create a unique filename for the layered image that includes the stroke ID
            String layeredPath = "project/" + projectId + "/original_" + strokeId + ".png";
            
            // Also save a copy as the standard layered path for backward compatibility
            String standardLayeredPath = "project/" + projectId + "/original_layered.png";
            
            // Load the images
            PImage originalImage = app.loadImage(inputPath);
            PImage effectImage = app.loadImage(outputPath);
            
            if (originalImage == null || effectImage == null) {
                System.err.println("Failed to load images for layering");
                return null;
            }
            
            // Create a new PImage with the same dimensions as the original
            PImage layeredImage = app.createImage(
                originalImage.width, 
                originalImage.height, 
                PConstants.ARGB
            );
            
            // Copy the original image to the layered image
            layeredImage.copy(
                originalImage, 
                0, 0, originalImage.width, originalImage.height, 
                0, 0, layeredImage.width, layeredImage.height
            );
            
            // Blend the effect image on top
            layeredImage.blend(
                effectImage, 
                0, 0, effectImage.width, effectImage.height, 
                0, 0, layeredImage.width, layeredImage.height, 
                PConstants.BLEND
            );
            
            // Save the layered image with the unique filename
            layeredImage.save(layeredPath);
            
            // Also save a copy as the standard layered path for backward compatibility
            layeredImage.save(standardLayeredPath);
            
            System.out.println("Successfully created layered image at: " + layeredPath);
            System.out.println("Also saved a copy at: " + standardLayeredPath);
            
            // Return the path to the unique layered image
            return layeredPath;
        } catch (Exception e) {
            System.err.println("Error creating layered image: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
    
    public boolean hasStrokes() {
        return !strokes.isEmpty();
    }

    private boolean isOutputImageValid(String projectId, String strokeId) {
        if (projectId == null || strokeId == null) {
            return false;
        }
        
        String outputPath = "project/" + projectId + "/stroke/" + strokeId + "_output.png";
        File outputFile = new File(outputPath);
        
        if (!outputFile.exists()) {
            System.err.println("Output image does not exist: " + outputPath);
            return false;
        }
        
        // Check if the file is a valid image
        try {
            PImage testImage = app.loadImage(outputPath);
            if (testImage == null || testImage.width <= 0 || testImage.height <= 0) {
                System.err.println("Output image is invalid or corrupted: " + outputPath);
                return false;
            }
            return true;
        } catch (Exception e) {
            System.err.println("Error validating output image: " + e.getMessage());
            return false;
        }
    }

    public boolean applyEffectToCanvas(String strokeId) {
        String projectId = app.getProjectId();
        if (projectId == null || strokeId == null) {
            System.err.println("Error: Project ID or Stroke ID is null");
            return false;
        }
        
        // Check if the effect was successful
        String instructionsPath = "project/" + projectId + "/stroke/" + 
                                 strokeId + "_instructions.json";
        File instructionsFile = new File(instructionsPath);
        
        if (!instructionsFile.exists()) {
            JOptionPane.showMessageDialog(
                null, 
                "Effect instructions not found. The stroke may be corrupted.", 
                "Error", 
                JOptionPane.ERROR_MESSAGE
            );
            return false;
        }
        
        JSONObject instructions = app.loadJSONObject(instructionsPath);
        String effectSuccess = instructions.getString("effect_success", "false");
        
        if (!"true".equals(effectSuccess)) {
            JOptionPane.showMessageDialog(
                null, 
                "Effect was not successfully processed. Please run the effect first.", 
                "Error", 
                JOptionPane.ERROR_MESSAGE
            );
            return false;
        }
        
        // First check if there's a specific layered image path in the instructions
        String layeredPath = instructions.getString("layered_output_location", null);
        File layeredFile = null;
        
        if (layeredPath != null) {
            layeredFile = new File(layeredPath);
        }
        
        // If no specific path or the file doesn't exist, check for the stroke-specific layered image
        if (layeredFile == null || !layeredFile.exists()) {
            layeredPath = "project/" + projectId + "/original_" + strokeId + ".png";
            layeredFile = new File(layeredPath);
        }
        
        // If that doesn't exist either, check for the standard layered image
        if (!layeredFile.exists()) {
            layeredPath = "project/" + projectId + "/original_layered.png";
            layeredFile = new File(layeredPath);
        }

        // If no layered file exists, create it
        if (!layeredFile.exists()) {
            layeredPath = createLayeredImage(projectId, strokeId);
            if (layeredPath != null) {
                layeredFile = new File(layeredPath);
            } else {
                JOptionPane.showMessageDialog(
                    null, 
                    "Could not create layered output image. Using standard output instead.", 
                    "Warning", 
                    JOptionPane.WARNING_MESSAGE
                );
            }
        }

        // Load and apply the layered output image if it exists, otherwise use the standard output
        PImage outputImage;
        if (layeredFile != null && layeredFile.exists()) {
            outputImage = app.loadImage(layeredPath);
        } else {
            // Get output image path from instructions
            JSONObject strokeInput = instructions.getJSONObject("stroke_input");
            String outputPath = strokeInput.getString("output_location", "");
            outputImage = app.loadImage(outputPath);
        }

        if (outputImage != null) {
            // Set as current image
            app.setCurrentImage(outputImage);
            
            // Save as new original
            String originalPath = "project/" + projectId + "/original.png";
            outputImage.save(originalPath);
            
            // Update project metadata
            app.getFileManager().updateProjectMetadata(projectId);
            
            // Clear paths
            app.getCanvasManager().clearPaths();
            
            JOptionPane.showMessageDialog(
                null, 
                "Effect applied to canvas successfully!", 
                "Success", 
                JOptionPane.INFORMATION_MESSAGE
            );
            
            return true;
        } else {
            JOptionPane.showMessageDialog(
                null, 
                "Failed to load output image.", 
                "Error", 
                JOptionPane.ERROR_MESSAGE
            );
            
            return false;
        }
    }
    
    /**
     * Cleans up resources when the application is closing.
     * This should be called when the application is shutting down.
     */
    public void shutdown() {
        // Cancel all running tasks
        for (Map.Entry<String, Future<?>> entry : processingStrokes.entrySet()) {
            entry.getValue().cancel(true);
        }
        
        // Shutdown the executor service
        executorService.shutdownNow();
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                System.err.println("Executor service did not terminate in the specified time.");
            }
        } catch (InterruptedException e) {
            System.err.println("Executor service shutdown interrupted: " + e.getMessage());
        }
    }

    class Stroke {
        private String id;
        private Effect effect;
        private Map<String, Object> parameters;
        private ArrayList<Path> paths;
        
        public Stroke(
            String id, 
            Effect effect, 
            Map<String, Object> parameters, 
            ArrayList<Path> paths
        ) {
            this.id = id;
            this.effect = effect;
            this.parameters = parameters;
            this.paths = new ArrayList<>(paths); // Make a copy of the paths
        }
        
        public String getId() {
            return id;
        }
        
        public Effect getEffect() {
            return effect;
        }
        
        public Map<String, Object> getParameters() {
            return parameters;
        }
        
        public ArrayList<Path> getPaths() {
            return paths;
        }
        
        public JSONObject generateJSON(String projectId) {
            JSONObject json = new JSONObject();
            
            // Add basic info
            json.setString("stroke_id", id);
            json.setString("project_id", projectId);
            json.setString("effect_id", effect.getId());
            
            // Add user input parameters
            JSONObject userInput = new JSONObject();
            JSONObject requirements = effect.getUserInputRequirements();
            
            for (Map.Entry<String, Object> entry : parameters.entrySet()) {
                String key = entry.getKey();
                Object value = entry.getValue();
                
                // Check if parameter exists in requirements
                if (requirements.hasKey(key)) {
                    Object defaultValue = requirements.get(key);
                    
                    // Handle color values
                    if (key.toLowerCase().contains("color") || 
                        (defaultValue instanceof String && 
                         ((String)defaultValue).startsWith("#"))) {
                        String colorStr = value.toString();
                        if (!colorStr.startsWith("#")) {
                            colorStr = "#" + colorStr.replaceAll("[^0-9A-Fa-f]", "");
                        }
                        userInput.setString(key, colorStr);
                    }
                    // Match type from requirements
                    else if (defaultValue instanceof Integer) {
                        try {
                            int intValue = (value instanceof Number) ? 
                                ((Number)value).intValue() : Integer.parseInt(value.toString());
                            userInput.setInt(key, intValue);
                        } catch (Exception e) {
                            userInput.setInt(key, (Integer)defaultValue);
                        }
                    } else if (defaultValue instanceof Float || defaultValue instanceof Double) {
                        try {
                            float floatValue = (value instanceof Number) ? 
                                ((Number)value).floatValue() : Float.parseFloat(value.toString());
                            userInput.setFloat(key, floatValue);
                        } catch (Exception e) {
                            float defaultFloat = defaultValue instanceof Float ? 
                                (Float)defaultValue : ((Double)defaultValue).floatValue();
                            userInput.setFloat(key, defaultFloat);
                        }
                    } else if (defaultValue instanceof Boolean) {
                        try {
                            boolean boolValue = (value instanceof Boolean) ? 
                                (Boolean)value : Boolean.parseBoolean(value.toString());
                            userInput.setBoolean(key, boolValue);
                        } catch (Exception e) {
                            userInput.setBoolean(key, (Boolean)defaultValue);
                        }
                    } else {
                        userInput.setString(key, value.toString());
                    }
                } else {
                    // Parameter not in requirements, use type inference
                    if (value instanceof Integer) {
                        userInput.setInt(key, (Integer) value);
                    } else if (value instanceof Float) {
                        userInput.setFloat(key, (Float) value);
                    } else if (value instanceof Double) {
                        userInput.setFloat(key, ((Double) value).floatValue());
                    } else if (value instanceof Boolean) {
                        userInput.setBoolean(key, (Boolean) value);
                    } else {
                        userInput.setString(key, value.toString());
                    }
                }
            }
            json.setJSONObject("user_input", userInput);
            
            // Add stroke input (path and clicks)
            JSONObject strokeInput = new JSONObject();
            strokeInput.setBoolean("real_hardware", false);
            
            // Create path array
            JSONArray pathArray = new JSONArray();
            for (Path path : paths) {
                ArrayList<PVector> points = path.getPoints();
                for (PVector point : points) {
                    JSONArray pointArray = new JSONArray();
                    pointArray.append(point.x);
                    pointArray.append(point.y);
                    pathArray.append(pointArray);
                }
            }
            strokeInput.setJSONArray("path", pathArray);
            
            // Add click points
            JSONArray clicksArray = new JSONArray();
            for (Path path : paths) {
                PVector clickPoint = path.getClickPoint();
                if (clickPoint != null) {
                    JSONArray clickArray = new JSONArray();
                    clickArray.append(clickPoint.x);
                    clickArray.append(clickPoint.y);
                    clicksArray.append(clickArray);
                }
            }
            strokeInput.setJSONArray("clicks", clicksArray);
            
            json.setJSONObject("stroke_input", strokeInput);
            
            // Add status fields
            json.setBoolean("created", true);
            json.setString("effect_received", "null");
            json.setString("effect_processed", "null");
            json.setString("effect_success", "null");
            json.setString("processing_status", "pending");
            
            return json;
        }
    }

    public void clearStrokes() {
        strokes.clear();
        currentStrokeIndex = -1;
        processingStrokes.clear();
    }
}
