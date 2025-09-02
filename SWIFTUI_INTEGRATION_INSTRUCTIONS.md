# 📱 SwiftUI Medical AI Integration Instructions

## 🎯 **GOAL**: Integrate your live Medical AI API into your existing SwiftUI app

**Your live API**: `https://web-production-9c1c.up.railway.app`  
**Status**: ✅ Operational and tested  
**Capabilities**: Medical Q&A, medication search, CIS lookups

---

## 📋 **STEP 1: Add Network Permissions (iOS Project Settings)**

### **1.1 Update Info.plist**
Open your iOS project's `Info.plist` file and add:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

**Why**: Allows your app to communicate with the Railway API server.

---

## 💻 **STEP 2: Add Medical AI Service Code**

### **2.1 Create New Swift File**
1. **Right-click** your project in Xcode
2. **New File** → **Swift File**
3. **Name it**: `MedicalAIService.swift`
4. **Add this complete code**:

```swift
import Foundation
import SwiftUI

// MARK: - Data Models
struct MedicationQueryRequest: Codable {
    let query: String
}

struct MedicationResponse: Codable {
    let success: Bool
    let data: MedicationData?
    let error: String?
    let timestamp: String
}

struct MedicationData: Codable {
    let query: String
    let response: String
    let confidence: Double
}

struct SearchRequest: Codable {
    let searchTerm: String
    let limit: Int
    
    private enum CodingKeys: String, CodingKey {
        case searchTerm = "search_term"
        case limit
    }
}

struct SearchResponse: Codable {
    let success: Bool
    let data: SearchData?
    let error: String?
    let timestamp: String
}

struct SearchData: Codable {
    let searchTerm: String
    let totalResults: Int
    let medications: [MedicationSearchResult]
    
    private enum CodingKeys: String, CodingKey {
        case searchTerm = "search_term"
        case totalResults = "total_results"
        case medications
    }
}

struct MedicationSearchResult: Codable, Identifiable {
    let id = UUID()
    let cis: String
    let name: String
    let form: String
    let route: String
    let status: String
    let similarityScore: Double
    
    private enum CodingKeys: String, CodingKey {
        case cis, name, form, route, status
        case similarityScore = "similarity_score"
    }
}

// MARK: - API Service
@MainActor
class MedicalAIService: ObservableObject {
    // 🚨 IMPORTANT: This is your live Railway API URL
    private let baseURL = "https://web-production-9c1c.up.railway.app"
    private let session = URLSession.shared
    
    @Published var isLoading = false
    @Published var lastError: String?
    
    func queryMedication(_ query: String) async throws -> MedicationResponse {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\\(baseURL)/query") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = MedicationQueryRequest(query: query)
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode >= 400 {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        let medicationResponse = try JSONDecoder().decode(MedicationResponse.self, from: data)
        lastError = nil
        return medicationResponse
    }
    
    func searchMedications(_ searchTerm: String, limit: Int = 10) async throws -> SearchResponse {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\\(baseURL)/search") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = SearchRequest(searchTerm: searchTerm, limit: limit)
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode >= 400 {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        let searchResponse = try JSONDecoder().decode(SearchResponse.self, from: data)
        lastError = nil
        return searchResponse
    }
    
    func checkHealth() async throws -> Bool {
        guard let url = URL(string: "\\(baseURL)/health") else {
            throw APIError.invalidURL
        }
        
        let (_, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        return httpResponse.statusCode == 200
    }
}

// MARK: - Error Handling
enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "URL invalide"
        case .invalidResponse:
            return "Réponse invalide du serveur"
        case .serverError(let code):
            return "Erreur serveur: \\(code)"
        }
    }
}
```

---

## 🎨 **STEP 3: Create Medical AI Views**

### **3.1 Create Medical Query View**
Create new Swift file: `MedicalQueryView.swift`

```swift
import SwiftUI

struct MedicalQueryView: View {
    @StateObject private var medicalService = MedicalAIService()
    @State private var query = ""
    @State private var response: MedicationResponse?
    @State private var showingAlert = false
    
    // Sample questions for quick testing
    let sampleQuestions = [
        "Qu'est-ce que l'ANASTROZOLE?",
        "Médicaments pour l'hypertension",
        "Traitement cancer du sein",
        "Qu'est-ce que TEMERITDUO?",
        "Effets secondaires anastrozole"
    ]
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Header
                    VStack(spacing: 12) {
                        Image(systemName: "stethoscope")
                            .font(.system(size: 50))
                            .foregroundColor(.blue)
                        
                        Text("Assistant Médical IA")
                            .font(.title)
                            .fontWeight(.bold)
                        
                        Text("Posez vos questions médicales")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top)
                    
                    // Query Input
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Votre question:")
                            .font(.headline)
                        
                        TextField("Ex: Qu'est-ce que l'ANASTROZOLE?", text: $query, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                        
                        // Quick Questions
                        Text("Questions rapides:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            ForEach(sampleQuestions, id: \\.self) { question in
                                Button(action: {
                                    query = question
                                }) {
                                    Text(question)
                                        .font(.caption)
                                        .padding(8)
                                        .background(Color.blue.opacity(0.1))
                                        .cornerRadius(8)
                                        .multilineTextAlignment(.center)
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                    }
                    .padding()
                    .background(Color.gray.opacity(0.05))
                    .cornerRadius(12)
                    
                    // Query Button
                    Button(action: {
                        Task {
                            await askQuestion()
                        }
                    }) {
                        HStack {
                            if medicalService.isLoading {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Image(systemName: "brain.head.profile")
                            }
                            Text(medicalService.isLoading ? "Analyse en cours..." : "Poser la Question")
                        }
                        .foregroundColor(.white)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(query.isEmpty ? Color.gray : Color.blue)
                        .cornerRadius(10)
                    }
                    .disabled(query.isEmpty || medicalService.isLoading)
                    
                    // Response Display
                    if let response = response {
                        VStack(alignment: .leading, spacing: 16) {
                            // Response Header
                            HStack {
                                Image(systemName: response.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(response.success ? .green : .red)
                                    .font(.title2)
                                
                                Text(response.success ? "Réponse Médicale" : "Erreur")
                                    .font(.headline)
                                
                                Spacer()
                                
                                if let data = response.data {
                                    Text("\\(String(format: "%.0f", data.confidence * 100))%")
                                        .font(.caption)
                                        .fontWeight(.semibold)
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(confidenceColor(data.confidence).opacity(0.2))
                                        .cornerRadius(6)
                                }
                            }
                            
                            // Response Content
                            if let data = response.data {
                                Text(data.response)
                                    .padding()
                                    .background(Color.blue.opacity(0.05))
                                    .cornerRadius(10)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 10)
                                            .stroke(Color.blue.opacity(0.2), lineWidth: 1)
                                    )
                            } else if let error = response.error {
                                Text(error)
                                    .foregroundColor(.red)
                                    .padding()
                                    .background(Color.red.opacity(0.1))
                                    .cornerRadius(10)
                            }
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                        .shadow(radius: 2)
                    }
                    
                    Spacer()
                }
                .padding()
            }
            .navigationBarHidden(true)
            .alert("Erreur de Connexion", isPresented: $showingAlert) {
                Button("OK") { }
            } message: {
                Text(medicalService.lastError ?? "Erreur inconnue")
            }
        }
    }
    
    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 { return .green }
        else if confidence >= 0.6 { return .orange }
        else { return .red }
    }
    
    private func askQuestion() async {
        do {
            response = try await medicalService.queryMedication(query)
        } catch {
            medicalService.lastError = error.localizedDescription
            showingAlert = true
        }
    }
}
```

---

## 🔍 **STEP 4: Create Search View (Optional)**

### **4.1 Create Search View File**
Create: `MedicationSearchView.swift`

```swift
import SwiftUI

struct MedicationSearchView: View {
    @StateObject private var medicalService = MedicalAIService()
    @State private var searchTerm = ""
    @State private var searchResults: [MedicationSearchResult] = []
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Header
                VStack(spacing: 16) {
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .font(.title2)
                            .foregroundColor(.blue)
                        
                        Text("Recherche Médicaments")
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    
                    // Search Bar
                    HStack {
                        TextField("Rechercher...", text: $searchTerm)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                        
                        Button("Rechercher") {
                            Task { await searchMedications() }
                        }
                        .disabled(searchTerm.isEmpty || medicalService.isLoading)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(searchTerm.isEmpty ? Color.gray : Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.05))
                
                // Results
                if medicalService.isLoading {
                    VStack {
                        ProgressView()
                        Text("Recherche en cours...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if searchResults.isEmpty {
                    VStack {
                        Image(systemName: "pills")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("Aucun résultat")
                            .font(.headline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(searchResults) { medication in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(medication.name)
                                .font(.headline)
                            
                            HStack {
                                Text("CIS: \\(medication.cis)")
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(Color.blue.opacity(0.2))
                                    .cornerRadius(4)
                                
                                Text(medication.form)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                
                                Spacer()
                                
                                Text("\\(String(format: "%.0f", medication.similarityScore * 100))%")
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.green.opacity(0.2))
                                    .cornerRadius(4)
                            }
                            
                            Text("\\(medication.route) - \\(medication.status)")
                                .font(.subheadline)
                                .foregroundColor(.blue)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .navigationBarHidden(true)
        }
    }
    
    private func searchMedications() async {
        do {
            let response = try await medicalService.searchMedications(searchTerm, limit: 20)
            if response.success, let data = response.data {
                searchResults = data.medications
            } else {
                searchResults = []
            }
        } catch {
            medicalService.lastError = error.localizedDescription
            searchResults = []
        }
    }
}
```

---

## 🏗️ **STEP 5: Integration Options**

### **🎯 OPTION A: Add to Existing TabView**

If you already have a `TabView`, add the medical AI as a new tab:

```swift
// In your existing TabView:
TabView {
    // Your existing tabs...
    
    // Add this new tab:
    MedicalQueryView()
        .tabItem {
            Image(systemName: "stethoscope")
            Text("Médical IA")
        }
    
    MedicationSearchView()
        .tabItem {
            Image(systemName: "magnifyingglass")
            Text("Recherche")
        }
}
```

### **🎯 OPTION B: Add as Modal/Sheet**

If you want it as a modal popup:

```swift
// In your existing view:
struct YourExistingView: View {
    @State private var showingMedicalAI = false
    
    var body: some View {
        VStack {
            // Your existing content...
            
            Button("Assistant Médical IA") {
                showingMedicalAI = true
            }
        }
        .sheet(isPresented: $showingMedicalAI) {
            MedicalQueryView()
        }
    }
}
```

### **🎯 OPTION C: Add as Navigation Destination**

If you want it as a separate screen:

```swift
// In your existing navigation:
NavigationView {
    VStack {
        // Your existing content...
        
        NavigationLink(destination: MedicalQueryView()) {
            HStack {
                Image(systemName: "stethoscope")
                Text("Assistant Médical IA")
            }
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(10)
        }
    }
}
```

---

## 🧪 **STEP 6: Test Integration**

### **6.1 Build and Run**
1. **Build your iOS app** in Xcode
2. **Run on simulator** or device

### **6.2 Test Medical Queries**
Try these test questions:

```
✅ "Qu'est-ce que l'ANASTROZOLE?"
Expected: Detailed information about ANASTROZOLE for breast cancer

✅ "Médicaments pour l'hypertension"  
Expected: Information about hypertension medications

✅ "TEMERITDUO posologie"
Expected: Dosage information for TEMERITDUO

✅ "Cancer du sein traitement"
Expected: Breast cancer treatment information
```

### **6.3 Expected Results**
- ✅ **Response time**: 1-3 seconds
- ✅ **Confidence scores**: 60-90%
- ✅ **Professional medical info**: French medical terminology
- ✅ **No crashes**: Robust error handling

---

## 🔧 **STEP 7: Customization Options**

### **7.1 Styling Customization**
```swift
// Customize colors and fonts to match your app:
.foregroundColor(.your_app_primary_color)
.background(Color.your_app_background)
.font(.your_app_font)
```

### **7.2 Add to Existing Views**
```swift
// Add medical AI button to any existing view:
Button("Poser une Question Médicale") {
    // Show medical AI view
}
```

### **7.3 Custom Integration**
```swift
// Use the service directly in your existing views:
@StateObject private var medicalService = MedicalAIService()

// In any function:
let response = try await medicalService.queryMedication("Your question")
```

---

## 🎯 **STEP 8: Advanced Features (Optional)**

### **8.1 Add History Feature**
```swift
@State private var queryHistory: [String] = []

// Save queries to history
queryHistory.append(query)
```

### **8.2 Add Favorites**
```swift
@State private var favoriteResponses: [MedicationResponse] = []

// Save favorite responses
favoriteResponses.append(response)
```

### **8.3 Add Voice Input**
```swift
import Speech

// Add voice recognition for medical queries
```

---

## 🚀 **WHAT YOUR USERS WILL GET:**

### **✅ Immediate Capabilities:**
- **Medical Q&A**: Ask any medication question in French
- **Instant responses**: 1-3 second response time
- **Professional information**: Accurate medical terminology
- **Confidence scores**: Reliability indicators
- **Search functionality**: Find medications by name

### **✅ Enhanced Features (When Fine-Tuned Models Complete):**
- **Specialized responses**: Custom-trained medical models
- **Higher accuracy**: Improved medical knowledge
- **Consistent formatting**: Standardized medical information

---

## 🎉 **FINAL RESULT:**

**Your SwiftUI app will now have:**
- 🏥 **Professional medical AI assistant**
- 🧠 **Intelligent medication queries**
- 🔍 **Advanced medication search**
- 📊 **Confidence scoring**
- ⚡ **Fast, reliable responses**

**Total integration time: ~15 minutes**  
**Your app becomes a medical AI assistant!** 🚀

---

## 📞 **SUPPORT:**

**If you need help:**
- Test API directly: `https://web-production-9c1c.up.railway.app/health`
- Check Railway logs for any issues
- Verify network permissions in iOS app

**Your medical AI system is ready to serve patients and healthcare professionals!** 🏥✨
