import XCTest
@testable import BootooMacCore

final class BootooMacCoreTests: XCTestCase {
    func testBootImageInitialization() {
        let image = BootImage(path: "/tmp/test.iso", format: "iso", sizeBytes: 1024)

        XCTAssertEqual(image.path, "/tmp/test.iso")
        XCTAssertEqual(image.format, "iso")
        XCTAssertEqual(image.sizeBytes, 1024)
    }
}
