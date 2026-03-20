import Foundation

public protocol PrivilegedExecutor {
    func run(_ command: String, args: [String], timeoutSeconds: Int) throws -> CommandResult
}

public final class ProcessExecutor: PrivilegedExecutor {
    public init() {}

    public func run(_ command: String, args: [String], timeoutSeconds: Int = 300) throws -> CommandResult {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: command)
        process.arguments = args

        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        try process.run()

        if timeoutSeconds > 0 {
            let finished = process.waitUntilExit(timeoutSeconds: timeoutSeconds)
            if !finished {
                process.terminate()
                throw CoreError(code: .commandTimeout, message: "Command timed out", details: command)
            }
        } else {
            process.waitUntilExit()
        }

        let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()

        let stdout = String(data: stdoutData, encoding: .utf8) ?? ""
        let stderr = String(data: stderrData, encoding: .utf8) ?? ""

        return CommandResult(exitCode: process.terminationStatus, stdout: stdout, stderr: stderr)
    }
}

private extension Process {
    func waitUntilExit(timeoutSeconds: Int) -> Bool {
        let group = DispatchGroup()
        group.enter()

        self.terminationHandler = { _ in
            group.leave()
        }

        let result = group.wait(timeout: .now() + .seconds(timeoutSeconds))
        return result == .success
    }
}
