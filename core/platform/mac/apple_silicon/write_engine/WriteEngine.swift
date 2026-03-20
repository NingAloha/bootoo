import Foundation

public protocol WriteEngine {
    func write(_ request: BootWriteRequest, onProgress: (BootWriteProgress) -> Void) throws
}

public final class BasicWriteEngine: WriteEngine {
    private let executor: PrivilegedExecutor
    private let logger: CoreLogger

    public init(executor: PrivilegedExecutor, logger: CoreLogger = ConsoleLogger()) {
        self.executor = executor
        self.logger = logger
    }

    public func write(_ request: BootWriteRequest, onProgress: (BootWriteProgress) -> Void) throws {
        try validateRequest(request)

        onProgress(BootWriteProgress(stage: .validating, percent: 0, detail: "Validating request"))
        onProgress(BootWriteProgress(stage: .unmounting, percent: 10, detail: "Unmounting target disk"))

        let unmountResult = try executor.run("/usr/sbin/diskutil", args: ["unmountDisk", request.device.path], timeoutSeconds: 60)
        guard unmountResult.exitCode == 0 else {
            throw CoreError(code: .deviceBusy, message: "Failed to unmount device", details: unmountResult.stderr)
        }

        onProgress(BootWriteProgress(stage: .writing, percent: 35, detail: "Writing image"))

        if request.dryRun {
            _ = try executor.run("/usr/bin/true", args: [], timeoutSeconds: 5)
            logger.log(level: .info, message: "Dry run write completed", metadata: ["device": request.device.path])
        } else {
            // TODO: Replace with real write command after safety checks are finalized.
            throw CoreError(code: .writeFailed, message: "Real write path is not implemented yet")
        }

        onProgress(BootWriteProgress(stage: .finalizing, percent: 90, detail: "Finalizing"))
        onProgress(BootWriteProgress(stage: .done, percent: 100, detail: "Completed"))
    }

    private func validateRequest(_ request: BootWriteRequest) throws {
        guard request.device.isExternal else {
            throw CoreError(code: .invalidDevice, message: "Target device must be external")
        }

        guard !request.device.isSystemDisk else {
            throw CoreError(code: .invalidDevice, message: "System disk cannot be written")
        }

        guard request.image.sizeBytes > 0 else {
            throw CoreError(code: .invalidImage, message: "Image size must be greater than zero")
        }

        guard request.image.sizeBytes <= request.device.sizeBytes else {
            throw CoreError(code: .invalidDevice, message: "Device capacity is smaller than image size")
        }
    }
}
