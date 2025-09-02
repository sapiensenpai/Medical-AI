// SwiftUI Integration for Medical AI API
// Copy this code into your SwiftUI project

import Foundation
import SwiftUI

// MARK: - Data Models

struct MedicationQueryRequest: Codable {
    let query: String
    let options: [String: String]?
    
    init(query: String, options: [String: String]? = nil) {
        self.query = query
        self.options = options
    }
}

struct MedicationResponse: Codable {
    let success: Bool
    let data: MedicationData?
    let error: String?
    let metadata: ResponseMetadata?
    let timestamp: String
}

struct MedicationData: Codable {
    let requestId: String
    let query: String
    let response: String
    let confidence: Double
    let approachUsed: String
    let modelUsed: String
    let sources: [String]
    
    private enum CodingKeys: String, CodingKey {
        case requestId = "request_id"
        case query, response, confidence
        case approachUsed = "approach_used"
        case modelUsed = "model_used"
        case sources
    }
}

struct ResponseMetadata: Codable {
    let responseTimeSeconds: Double
    let endpoint: String
    
    private enum CodingKeys: String, CodingKey {
        case responseTimeSeconds = "response_time_seconds"
        case endpoint
    }
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
    let metadata: ResponseMetadata?
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
    let components: [MedicationComponent]
    
    private enum CodingKeys: String, CodingKey {
        case cis, name, form, route, status
        case similarityScore = "similarity_score"
        case components
    }
}

struct MedicationComponent: Codable {
    let dosage: String
    let refDosage: String
    let nature: String
    
    private enum CodingKeys: String, CodingKey {
        case dosage
        case refDosage = "ref_dosage"
        case nature
    }
}

// MARK: - API Service

@MainActor
class MedicalAIService: ObservableObject {
    private let baseURL: String
    private let session = URLSession.shared
    
    @Published var isLoading = false
    @Published var lastError: String?
    
    init(baseURL: String = "http://127.0.0.1:5000") {
        self.baseURL = baseURL
    }
    
    func queryMedication(_ query: String) async throws -> MedicationResponse {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\(baseURL)/query") else {
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
            // Try to parse error response
            if let errorResponse = try? JSONDecoder().decode(MedicationResponse.self, from: data) {
                lastError = errorResponse.error
                return errorResponse
            } else {
                throw APIError.serverError(httpResponse.statusCode)
            }
        }
        
        let medicationResponse = try JSONDecoder().decode(MedicationResponse.self, from: data)
        lastError = nil
        return medicationResponse
    }
    
    func searchMedications(_ searchTerm: String, limit: Int = 10) async throws -> SearchResponse {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\(baseURL)/search") else {
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
    
    func getMedicationByCIS(_ cisCode: String) async throws -> MedicationResponse {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\(baseURL)/medication/\(cisCode)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
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
    
    func checkHealth() async throws -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
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
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}

// MARK: - SwiftUI Views

struct MedicationQueryView: View {
    @StateObject private var medicalService = MedicalAIService()
    @State private var query = ""
    @State private var response: MedicationResponse?
    @State private var showingAlert = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Query Input
                VStack(alignment: .leading, spacing: 8) {
                    Text("Question médicale:")
                        .font(.headline)
                    
                    TextField("Posez votre question sur un médicament...", text: $query, axis: .vertical)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .lineLimit(3...6)
                }
                
                // Query Button
                Button(action: {
                    Task {
                        await queryMedication()
                    }
                }) {
                    HStack {
                        if medicalService.isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "stethoscope")
                        }
                        Text("Interroger l'IA Médicale")
                    }
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(10)
                }
                .disabled(query.isEmpty || medicalService.isLoading)
                
                // Response Display
                if let response = response {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 12) {
                            // Response Header
                            HStack {
                                Image(systemName: response.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(response.success ? .green : .red)
                                
                                Text(response.success ? "Réponse" : "Erreur")
                                    .font(.headline)
                                
                                Spacer()
                                
                                if let data = response.data {
                                    Text("Confiance: \(String(format: "%.0f", data.confidence * 100))%")
                                        .font(.caption)
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(Color.blue.opacity(0.2))
                                        .cornerRadius(8)
                                }
                            }
                            
                            // Response Content
                            if let data = response.data {
                                Text(data.response)
                                    .padding()
                                    .background(Color.gray.opacity(0.1))
                                    .cornerRadius(8)
                                
                                // Metadata
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Modèle utilisé: \(data.modelUsed)")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    
                                    Text("Sources: \(data.sources.joined(separator: ", "))")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    
                                    if let metadata = response.metadata {
                                        Text("Temps de réponse: \(String(format: "%.2f", metadata.responseTimeSeconds))s")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            } else if let error = response.error {
                                Text(error)
                                    .foregroundColor(.red)
                                    .padding()
                                    .background(Color.red.opacity(0.1))
                                    .cornerRadius(8)
                            }
                        }
                    }
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Assistant Médical IA")
            .alert("Erreur", isPresented: $showingAlert) {
                Button("OK") { }
            } message: {
                Text(medicalService.lastError ?? "Erreur inconnue")
            }
        }
    }
    
    private func queryMedication() async {
        do {
            response = try await medicalService.queryMedication(query)
        } catch {
            medicalService.lastError = error.localizedDescription
            showingAlert = true
        }
    }
}

// MARK: - Search View

struct MedicationSearchView: View {
    @StateObject private var medicalService = MedicalAIService()
    @State private var searchTerm = ""
    @State private var searchResults: [MedicationSearchResult] = []
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                HStack {
                    TextField("Rechercher un médicament...", text: $searchTerm)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button("Rechercher") {
                        Task {
                            await searchMedications()
                        }
                    }
                    .disabled(searchTerm.isEmpty || medicalService.isLoading)
                }
                .padding()
                
                // Results List
                List(searchResults) { medication in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(medication.name)
                            .font(.headline)
                        
                        Text("CIS: \(medication.cis)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("\(medication.form) - \(medication.route)")
                            .font(.subheadline)
                            .foregroundColor(.blue)
                        
                        Text("Score: \(String(format: "%.1f", medication.similarityScore * 100))%")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.green.opacity(0.2))
                            .cornerRadius(4)
                    }
                    .padding(.vertical, 4)
                }
            }
            .navigationTitle("Recherche Médicaments")
        }
    }
    
    private func searchMedications() async {
        do {
            let response = try await medicalService.searchMedications(searchTerm, limit: 20)
            if response.success, let data = response.data {
                searchResults = data.medications
            }
        } catch {
            medicalService.lastError = error.localizedDescription
        }
    }
}

// MARK: - Main App View

struct MedicalAIApp: View {
    var body: some View {
        TabView {
            MedicationQueryView()
                .tabItem {
                    Image(systemName: "questionmark.circle")
                    Text("Questions")
                }
            
            MedicationSearchView()
                .tabItem {
                    Image(systemName: "magnifyingglass")
                    Text("Recherche")
                }
        }
    }
}

// MARK: - Preview

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        MedicalAIApp()
    }
}
