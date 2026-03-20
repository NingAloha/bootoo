import Foundation

public enum CoreLogLevel: String {
    case debug
    case info
    case warn
    case error
}

public protocol CoreLogger {
    func log(level: CoreLogLevel, message: String, metadata: [String: String])
}

public struct ConsoleLogger: CoreLogger {
    private let dateFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    public init() {}

    public func log(level: CoreLogLevel, message: String, metadata: [String: String] = [:]) {
        let timestamp = dateFormatter.string(from: Date())
        if metadata.isEmpty {
            print("[\(timestamp)] [\(level.rawValue.uppercased())] \(message)")
            return
        }

        let details = metadata
            .sorted { $0.key < $1.key }
            .map { "\($0.key)=\($0.value)" }
            .joined(separator: " ")
        print("[\(timestamp)] [\(level.rawValue.uppercased())] \(message) \(details)")
    }
}
