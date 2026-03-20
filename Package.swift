// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "bootoo",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "BootooMacCore",
            targets: ["BootooMacCore"]
        )
    ],
    targets: [
        .target(
            name: "BootooMacCore",
            path: "core/platform/mac/apple_silicon",
            exclude: [
                "README.md",
                "development_plan.md"
            ]
        ),
        .testTarget(
            name: "BootooMacCoreTests",
            dependencies: ["BootooMacCore"],
            path: "tests/mac/apple_silicon"
        )
    ]
)
