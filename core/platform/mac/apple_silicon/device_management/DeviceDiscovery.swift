import Foundation

public protocol DeviceDiscovery {
    func listWritableDevices() throws -> [BootDiskDevice]
}

public final class DeviceDiscoveryService: DeviceDiscovery {
    public init() {}

    public func listWritableDevices() throws -> [BootDiskDevice] {
        // TODO: Parse diskutil output and convert to BootDiskDevice values.
        return []
    }
}
