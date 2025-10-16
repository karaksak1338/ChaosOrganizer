import SwiftUI
import UniformTypeIdentifiers

struct Doc: Identifiable, Codable {
    let id: String
    let file_name: String
    let file_url: String?
    let category: String?
    let doc_type: String?
    let supplier: String?
    let issue_date: String?
    let amount: Double?
    let ai_confidence: Double?
    let created_at: String?
    let updated_at: String?
    let deleted_at: String?
    let user_id: String?
}
class API: ObservableObject {
    let base = "http://localhost:8000"
    let userId = "00000000-0000-0000-0000-000000000001"
    @Published var docs: [Doc] = []
    var headers: [String:String] { ["X-User-Id": userId] }
    func load(){
        guard let url = URL(string: "\(base)/api/documents") else { return }
        var req = URLRequest(url: url); headers.forEach{ req.setValue($0.value, forHTTPHeaderField: $0.key) }
        URLSession.shared.dataTask(with: req){ data,_,_ in
            if let data = data, let list = try? JSONDecoder().decode([Doc].self, from: data){
                DispatchQueue.main.async{ self.docs = list }
            }
        }.resume()
    }
    func signedUrl(id: String, completion: @escaping (URL?)->Void){
        guard let url = URL(string: "\(base)/api/signed-url/\(id)") else { completion(nil); return }
        var req = URLRequest(url: url); headers.forEach{ req.setValue($0.value, forHTTPHeaderField: $0.key) }
        URLSession.shared.dataTask(with: req){ data,_,_ in
            if let data = data,
               let j = try? JSONSerialization.jsonObject(with: data) as? [String:Any],
               let s = j["url"] as? String, let u = URL(string:s){
                completion(u)
            } else { completion(nil) }
        }.resume()
    }
    func deleteDoc(id: String){
        guard let url = URL(string: "\(base)/api/documents/\(id)") else { return }
        var req = URLRequest(url: url); req.httpMethod = "DELETE"
        headers.forEach{ req.setValue($0.value, forHTTPHeaderField: $0.key) }
        URLSession.shared.dataTask(with: req){ data,_,_ in
            guard let data = data,
                  let first = try? JSONSerialization.jsonObject(with: data) as? [String:Any] else { return }
            if (first["confirm"] as? Bool) == true {
                if let url2 = URL(string: "\(self.base)/api/documents/\(id)?confirm=true"){
                    var r2 = URLRequest(url: url2); r2.httpMethod = "DELETE"
                    self.headers.forEach{ r2.setValue($0.value, forHTTPHeaderField: $0.key) }
                    URLSession.shared.dataTask(with: r2){_,_,_ in DispatchQueue.main.async{ self.load() } }.resume()
                }
            } else {
                DispatchQueue.main.async{ self.load() }
            }
        }.resume()
    }
    func upload(url: URL){
        guard let reqURL = URL(string: "\(base)/api/upload") else { return }
        var req = URLRequest(url: reqURL); req.httpMethod = "POST"
        headers.forEach{ req.setValue($0.value, forHTTPHeaderField: $0.key) }
        let boundary = "Boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        var data = Data()
        let filename = url.lastPathComponent
        let fieldName = "file"
        let mimeType = "application/octet-stream"
        data.append("--\(boundary)\r\n".data(using:.utf8)!)
        data.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(filename)\"\r\n".data(using:.utf8)!)
        data.append("Content-Type: \(mimeType)\r\n\r\n".data(using:.utf8)!)
        if let fileData = try? Data(contentsOf: url){ data.append(fileData) }
        data.append("\r\n--\(boundary)--\r\n".data(using:.utf8)!)
        URLSession.shared.uploadTask(with: req, from: data){_,_,_ in DispatchQueue.main.async{ self.load() } }.resume()
    }
}
struct ContentView: View {
    @StateObject var api = API()
    @State private var isPickerPresented = false
    var body: some View {
        NavigationView{
            List{
                ForEach(api.docs){ d in
                    VStack(alignment:.leading){
                        HStack{
                            Text(d.file_name).font(.headline)
                            Spacer()
                            Button("Open"){ open(doc:d) }
                            Button(role:.destructive){ confirmDelete(id:d.id) } label{ Text("Delete") }
                        }
                        Text("Type: \(d.doc_type ?? "-") | Category: \(d.category ?? "-") | Supplier: \(d.supplier ?? "-")")
                            .font(.subheadline).foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("ChaosOrganizer")
            .toolbar{ ToolbarItem(placement:.navigationBarTrailing){ Button{ isPickerPresented=true } label{ Image(systemName:"plus") } } }
            .onAppear{ api.load() }
            .fileImporter(isPresented:$isPickerPresented, allowedContentTypes:[.pdf, .image]){ result in
                if case let .success(url) = result { api.upload(url:url) }
            }
        }
    }
    func open(doc: Doc){
        api.signedUrl(id: doc.id){ url in if let url = url { DispatchQueue.main.async{ UIApplication.shared.open(url) } } }
    }
    func confirmDelete(id: String){
        let alert = UIAlertController(title:"Confirm Deletion", message:"Are you sure you want to delete this document?", preferredStyle:.alert)
        alert.addAction(UIAlertAction(title:"Cancel", style:.cancel))
        alert.addAction(UIAlertAction(title:"Delete", style:.destructive, handler:{ _ in api.deleteDoc(id:id) }))
        UIApplication.shared.windows.first?.rootViewController?.present(alert, animated:true)
    }
}
