import Foundation

public protocol ImageValidator {
    func validateImage(at path: String) throws -> BootImage
}

public final class BasicImageValidator: ImageValidator {
    private let supportedExtensions: Set<String> = ["iso", "img"]

    public init() {}

    public func validateImage(at path: String) throws -> BootImage {
        let url = URL(fileURLWithPath: path)
        let ext = url.pathExtension.lowercased()

        guard supportedExtensions.contains(ext) else {
            throw CoreError(
                code: .invalidImage,
                message: "Unsupported image format",
                details: "Expected one of: \(supportedExtensions.sorted().joined(separator: ", "))"
            )
        }

        let fileManager = FileManager.default
        guard fileManager.fileExists(atPath: path) else {
            throw CoreError(code: .invalidImage, message: "Image file does not exist", details: path)
        }

        let attrs = try fileManager.attributesOfItem(atPath: path)
        guard let size = attrs[.size] as? NSNumber else {
            throw CoreError(code: .invalidImage, message: "Unable to read image size")
        }

        return BootImage(path: path, format: ext, sizeBytes: size.uint64Value)
    }
}
