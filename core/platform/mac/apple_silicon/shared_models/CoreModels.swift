import Foundation

public struct BootDiskDevice: Equatable {
    public let id: String
    public let path: String
    public let name: String
    public let sizeBytes: UInt64
    public let isExternal: Bool
    public let isSystemDisk: Bool
    public let isMounted: Bool

    public init(
        id: String,
        path: String,
        name: String,
        sizeBytes: UInt64,
        isExternal: Bool,
        isSystemDisk: Bool,
        isMounted: Bool
    ) {
        self.id = id
        self.path = path
        self.name = name
        self.sizeBytes = sizeBytes
        self.isExternal = isExternal
        self.isSystemDisk = isSystemDisk
        self.isMounted = isMounted
    }
}

public struct BootImage: Equatable {
    public let path: String
    public let format: String
    public let sizeBytes: UInt64

    public init(path: String, format: String, sizeBytes: UInt64) {
        self.path = path
        self.format = format
        self.sizeBytes = sizeBytes
    }
}

public enum BootWriteStage: String, CaseIterable {
    case validating
    case unmounting
    case writing
    case verifying
    case finalizing
    case done
}

public struct BootWriteProgress: Equatable {
    public let stage: BootWriteStage
    public let percent: Double
    public let detail: String

    public init(stage: BootWriteStage, percent: Double, detail: String) {
        self.stage = stage
        self.percent = percent
        self.detail = detail
    }
}

public struct BootWriteRequest: Equatable {
    public let image: BootImage
    public let device: BootDiskDevice
    public let dryRun: Bool

    public init(image: BootImage, device: BootDiskDevice, dryRun: Bool = true) {
        self.image = image
        self.device = device
        self.dryRun = dryRun
    }
}

public struct CommandResult: Equatable {
    public let exitCode: Int32
    public let stdout: String
    public let stderr: String

    public init(exitCode: Int32, stdout: String, stderr: String) {
        self.exitCode = exitCode
        self.stdout = stdout
        self.stderr = stderr
    }
}
