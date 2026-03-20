import Foundation

public enum CoreErrorCode: String, Sendable {
    case permissionDenied
    case deviceNotFound
    case deviceBusy
    case invalidImage
    case invalidDevice
    case writeFailed
    case commandTimeout
    case commandFailed
    case internalError
}

public struct CoreError: Error, Equatable {
    public let code: CoreErrorCode
    public let message: String
    public let details: String?

    public init(code: CoreErrorCode, message: String, details: String? = nil) {
        self.code = code
        self.message = message
        self.details = details
    }
}

extension CoreError: LocalizedError {
    public var errorDescription: String? {
        if let details, !details.isEmpty {
            return "[\(code.rawValue)] \(message): \(details)"
        }
        return "[\(code.rawValue)] \(message)"
    }
}
